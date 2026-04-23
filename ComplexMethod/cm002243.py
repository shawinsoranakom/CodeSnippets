def main():
    # See all possible arguments in src/transformers/args.py
    # or by passing the --help flag to this script.
    # We now keep distinct sets of args, for a cleaner separation of concerns.
    args = parse_args()

    # Initialize the accelerator. We will let the accelerator handle device placement for us in this example.
    accelerator = Accelerator()
    logger.info(accelerator.state, main_process_only=False)
    if accelerator.is_local_main_process:
        datasets.utils.logging.set_verbosity_warning()
        transformers.utils.logging.set_verbosity_info()

        # set up weights and biases if available
        if is_wandb_available():
            import wandb

            wandb.init(project=args.output_dir.split("/")[-1])
    else:
        datasets.utils.logging.set_verbosity_error()
        transformers.utils.logging.set_verbosity_error()

    # If passed along, set the training seed now.
    if args.seed is not None:
        set_seed(args.seed)

    # Handle the repository creation
    if accelerator.is_main_process:
        if args.push_to_hub and not args.preprocessing_only:
            # Retrieve of infer repo_name
            repo_name = args.hub_model_id
            if repo_name is None:
                repo_name = Path(args.output_dir).absolute().name
            # Create repo and retrieve repo_id
            api = HfApi()
            repo_id = api.create_repo(repo_name, exist_ok=True, token=args.hub_token).repo_id

            with open(os.path.join(args.output_dir, ".gitignore"), "w+") as gitignore:
                if "step_*" not in gitignore:
                    gitignore.write("step_*\n")
                if "epoch_*" not in gitignore:
                    gitignore.write("epoch_*\n")
        elif args.output_dir is not None:
            os.makedirs(args.output_dir, exist_ok=True)
    accelerator.wait_for_everyone()

    # 1. Download and create train, validation dataset
    # We load all dataset configuration and dataset split pairs passed in
    # ``args.dataset_config_names`` and ``args.dataset_split_names``
    datasets_splits = []
    for dataset_config_name, train_split_name in zip(args.dataset_config_names, args.dataset_split_names):
        # load dataset
        dataset_split = load_dataset(
            args.dataset_name,
            dataset_config_name,
            split=train_split_name,
            cache_dir=args.cache_dir,
            trust_remote_code=args.trust_remote_code,
            storage_options={"client_kwargs": {"timeout": aiohttp.ClientTimeout(total=60 * 60)}},
        )
        datasets_splits.append(dataset_split)

    # Next, we concatenate all configurations and splits into a single training dataset
    raw_datasets = DatasetDict()
    if len(datasets_splits) > 1:
        raw_datasets["train"] = concatenate_datasets(datasets_splits).shuffle(seed=args.seed)
    else:
        raw_datasets["train"] = datasets_splits[0]

    # Take ``args.validation_split_percentage`` from the training dataset for the validation_split_percentage
    num_validation_samples = raw_datasets["train"].num_rows * args.validation_split_percentage // 100

    if num_validation_samples == 0:
        raise ValueError(
            "`args.validation_split_percentage` is less than a single sample "
            f"for {len(raw_datasets['train'])} training samples. Increase "
            "`args.num_validation_split_percentage`. "
        )

    raw_datasets["validation"] = raw_datasets["train"].select(range(num_validation_samples))
    raw_datasets["train"] = raw_datasets["train"].select(range(num_validation_samples, raw_datasets["train"].num_rows))

    # 2. Now we preprocess the datasets including loading the audio, resampling and normalization
    # Thankfully, `datasets` takes care of automatically loading and resampling the audio,
    # so that we just need to set the correct target sampling rate and normalize the input
    # via the `feature_extractor`
    feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(args.model_name_or_path)

    # make sure that dataset decodes audio with correct sampling rate
    raw_datasets = raw_datasets.cast_column(
        args.audio_column_name, datasets.features.Audio(sampling_rate=feature_extractor.sampling_rate)
    )

    # only normalized-inputs-training is supported
    if not feature_extractor.do_normalize:
        raise ValueError(
            "Training is only supported for normalized inputs. Make sure ``feature_extractor.do_normalize == True``"
        )

    # set max & min audio length in number of samples
    max_length = int(args.max_duration_in_seconds * feature_extractor.sampling_rate)
    min_length = int(args.min_duration_in_seconds * feature_extractor.sampling_rate)

    def prepare_dataset(batch):
        sample = batch[args.audio_column_name]

        inputs = feature_extractor(
            sample["array"], sampling_rate=sample["sampling_rate"], max_length=max_length, truncation=True
        )
        batch["input_values"] = inputs.input_values[0]
        batch["input_length"] = len(inputs.input_values[0])

        return batch

    # load via mapped files via path
    cache_file_names = None
    if args.train_cache_file_name is not None:
        cache_file_names = {"train": args.train_cache_file_name, "validation": args.validation_cache_file_name}

    # load audio files into numpy arrays
    with accelerator.main_process_first():
        vectorized_datasets = raw_datasets.map(
            prepare_dataset,
            num_proc=args.preprocessing_num_workers,
            remove_columns=raw_datasets["train"].column_names,
            cache_file_names=cache_file_names,
        )

        if min_length > 0.0:
            vectorized_datasets = vectorized_datasets.filter(
                lambda x: x > min_length,
                num_proc=args.preprocessing_num_workers,
                input_columns=["input_length"],
            )

        vectorized_datasets = vectorized_datasets.remove_columns("input_length")

    # for large datasets it is advised to run the preprocessing on a
    # single machine first with ``args.preprocessing_only`` since there will mostly likely
    # be a timeout when running the script in distributed mode.
    # In a second step ``args.preprocessing_only`` can then be set to `False` to load the
    # cached dataset
    if args.preprocessing_only:
        return

    # 3. Load model
    config = Wav2Vec2Config.from_pretrained(args.model_name_or_path)

    # pretraining is only supported for "newer" stable layer norm architecture
    # apply_spec_augment has to be True, mask_feature_prob has to be 0.0
    if not config.do_stable_layer_norm or config.feat_extract_norm != "layer":
        raise ValueError(
            "PreTraining is only supported for ``config.do_stable_layer_norm=True`` and"
            " ``config.feat_extract_norm='layer'"
        )

    # initialize random model
    model = Wav2Vec2ForPreTraining(config)

    # Activate gradient checkpointing if needed
    if args.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    # 4. Define data collator, optimizer and scheduler

    mask_time_prob = config.mask_time_prob if args.mask_time_prob is None else args.mask_time_prob
    mask_time_length = config.mask_time_length if args.mask_time_length is None else args.mask_time_length

    data_collator = DataCollatorForWav2Vec2Pretraining(
        model=model,
        feature_extractor=feature_extractor,
        pad_to_multiple_of=args.pad_to_multiple_of,
        mask_time_prob=mask_time_prob,
        mask_time_length=mask_time_length,
    )
    train_dataloader = DataLoader(
        vectorized_datasets["train"],
        shuffle=True,
        collate_fn=data_collator,
        batch_size=args.per_device_train_batch_size,
    )
    eval_dataloader = DataLoader(
        vectorized_datasets["validation"], collate_fn=data_collator, batch_size=args.per_device_eval_batch_size
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        list(model.parameters()),
        lr=args.learning_rate,
        betas=[args.adam_beta1, args.adam_beta2],
        eps=args.adam_epsilon,
    )

    # Prepare everything with our `accelerator`.
    model, optimizer, train_dataloader, eval_dataloader = accelerator.prepare(
        model, optimizer, train_dataloader, eval_dataloader
    )

    # Scheduler and math around the number of training steps.
    num_update_steps_per_epoch = math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)

    if args.max_train_steps is None:
        args.max_train_steps = args.num_train_epochs * num_update_steps_per_epoch

    lr_scheduler = get_scheduler(
        name=args.lr_scheduler_type,
        optimizer=optimizer,
        num_warmup_steps=args.num_warmup_steps,
        num_training_steps=args.max_train_steps,
    )

    # Afterwards we recalculate our number of training epochs
    args.num_train_epochs = math.ceil(args.max_train_steps / num_update_steps_per_epoch)

    # 5. Train
    total_batch_size = args.per_device_train_batch_size * accelerator.num_processes * args.gradient_accumulation_steps

    logger.info("***** Running training *****")
    logger.info(f"  Num examples = {len(vectorized_datasets['train'])}")
    logger.info(f"  Num Epochs = {args.num_train_epochs}")
    logger.info(f"  Instantaneous batch size per device = {args.per_device_train_batch_size}")
    logger.info(f"  Total train batch size (w. parallel, distributed & accumulation) = {total_batch_size}")
    logger.info(f"  Gradient Accumulation steps = {args.gradient_accumulation_steps}")
    logger.info(f"  Total optimization steps = {args.max_train_steps}")
    completed_steps = 0
    starting_epoch = 0

    # Only show the progress bar once on each machine.
    progress_bar = tqdm(range(args.max_train_steps), disable=not accelerator.is_local_main_process)
    completed_steps = 0
    starting_epoch = 0
    for epoch in range(starting_epoch, args.num_train_epochs):
        model.train()
        for step, batch in enumerate(train_dataloader):
            # compute num of losses
            num_losses = batch["mask_time_indices"].sum()
            sub_attention_mask = batch.pop("sub_attention_mask", None)
            sub_attention_mask = (
                sub_attention_mask if sub_attention_mask is not None else torch.ones_like(batch["mask_time_indices"])
            )
            percent_masked = num_losses / sub_attention_mask.sum()

            # forward
            outputs = model(**batch)

            # divide loss by gradient accumulation steps since gradients
            # are accumulated for multiple backward passes in PyTorch
            loss = outputs.loss / args.gradient_accumulation_steps
            accelerator.backward(loss)

            # make sure that `num_losses` is summed for distributed training
            # and average gradients over losses of all devices
            if accelerator.state.num_processes > 1:
                num_losses = accelerator.gather_for_metrics(num_losses).sum()
                gradient_multiplier = accelerator.state.num_processes / num_losses
                multiply_grads(model.module.parameters(), gradient_multiplier)
            else:
                multiply_grads(model.parameters(), 1 / num_losses)

            # update step
            if (step + 1) % args.gradient_accumulation_steps == 0 or step == len(train_dataloader) - 1:
                # compute grad norm for monitoring
                scale = (
                    accelerator.scaler._scale.item()
                    if hasattr(accelerator, "scaler") and accelerator.scaler is not None
                    else 1
                )
                if accelerator.state.num_processes > 1:
                    grad_norm = get_grad_norm(model.module.parameters(), scale)
                else:
                    grad_norm = get_grad_norm(model.parameters(), scale)

                # update parameters
                optimizer.step()
                optimizer.zero_grad()

                if not accelerator.optimizer_step_was_skipped:
                    lr_scheduler.step()
                elif accelerator.is_local_main_process:
                    progress_bar.write(
                        f"Gradients have overflown - skipping update step... Updating gradient scale to {scale}..."
                    )

                # update gumbel temperature
                gumbel_temperature = max(
                    args.max_gumbel_temperature * args.gumbel_temperature_decay**completed_steps,
                    args.min_gumbel_temperature,
                )
                if hasattr(model, "module"):
                    model.module.set_gumbel_temperature(gumbel_temperature)
                else:
                    model.set_gumbel_temperature(gumbel_temperature)

                progress_bar.update(1)
                completed_steps += 1

            # 6. Log all results
            if (step + 1) % (args.gradient_accumulation_steps * args.logging_steps) == 0:
                loss.detach()
                outputs.contrastive_loss.detach()
                outputs.diversity_loss.detach()

                if accelerator.state.num_processes > 1:
                    loss = accelerator.gather_for_metrics(loss).sum()
                    outputs.contrastive_loss = accelerator.gather_for_metrics(outputs.contrastive_loss).sum()
                    outputs.diversity_loss = accelerator.gather_for_metrics(outputs.diversity_loss).sum()
                    percent_masked = accelerator.gather_for_metrics(percent_masked).sum()

                train_logs = {
                    "loss": (loss * args.gradient_accumulation_steps) / num_losses,
                    "constrast_loss": outputs.contrastive_loss / num_losses,
                    "div_loss": outputs.diversity_loss / num_losses,
                    "%_mask_idx": percent_masked / accelerator.num_processes,
                    "ppl": outputs.codevector_perplexity,
                    "lr": torch.tensor(optimizer.param_groups[0]["lr"]),
                    "temp": torch.tensor(gumbel_temperature),
                    "grad_norm": torch.tensor(grad_norm),
                }
                log_str = ""
                for k, v in train_logs.items():
                    log_str += f"| {k}: {v.item():.3e}"

                if accelerator.is_local_main_process:
                    progress_bar.write(log_str)
                    if is_wandb_available():
                        wandb.log(train_logs)

            # save model every `args.saving_steps` steps
            if (step + 1) % (args.gradient_accumulation_steps * args.saving_steps) == 0:
                if (args.push_to_hub and epoch < args.num_train_epochs - 1) or args.output_dir is not None:
                    accelerator.wait_for_everyone()
                    unwrapped_model = accelerator.unwrap_model(model)
                    unwrapped_model.save_pretrained(
                        args.output_dir, is_main_process=accelerator.is_main_process, save_function=accelerator.save
                    )

                if (args.push_to_hub and epoch < args.num_train_epochs - 1) and accelerator.is_main_process:
                    api.upload_folder(
                        commit_message=f"Training in progress epoch {epoch}",
                        folder_path=args.output_dir,
                        repo_id=repo_id,
                        repo_type="model",
                        token=args.hub_token,
                    )

            # if completed steps > `args.max_train_steps` stop
            if completed_steps >= args.max_train_steps:
                break

        # 7. Validate!
        model.eval()

        # init logs
        val_logs = {
            "val_loss": 0,
            "val_contrastive_loss": 0,
            "val_diversity_loss": 0,
            "val_num_losses": 0,
        }
        for step, batch in enumerate(eval_dataloader):
            with torch.no_grad():
                batch.pop("sub_attention_mask", None)
                outputs = model(**batch)

            val_logs["val_loss"] += outputs.loss
            val_logs["val_contrastive_loss"] += outputs.contrastive_loss
            val_logs["val_diversity_loss"] += outputs.diversity_loss
            val_logs["val_num_losses"] += batch["mask_time_indices"].sum()

        # sum over devices in multi-processing
        if accelerator.num_processes > 1:
            val_logs = {k: accelerator.gather_for_metrics(v).sum() for k, v in val_logs.items()}

        val_logs = {k: v / val_logs["val_num_losses"] for k, v in val_logs.items()}

        log_str = ""
        for k, v in val_logs.items():
            log_str += f"| {k}: {v.item():.3e}"

        if accelerator.is_local_main_process:
            progress_bar.write(log_str)
            if is_wandb_available():
                wandb.log(val_logs)

        if args.output_dir is not None:
            accelerator.wait_for_everyone()
            unwrapped_model = accelerator.unwrap_model(model)
            unwrapped_model.save_pretrained(
                args.output_dir, is_main_process=accelerator.is_main_process, save_function=accelerator.save
            )
            if accelerator.is_main_process:
                if args.push_to_hub:
                    api.upload_folder(
                        commit_message="End of training",
                        folder_path=args.output_dir,
                        repo_id=repo_id,
                        repo_type="model",
                        token=args.hub_token,
                    )