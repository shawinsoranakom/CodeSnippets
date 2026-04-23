def main():
    args = parse_args()

    # Initialize the accelerator. We will let the accelerator handle device placement for us in this example.
    # If we're using tracking, we also need to initialize it here and it will by default pick up all supported trackers
    # in the environment
    accelerator_log_kwargs = {}

    if args.with_tracking:
        accelerator_log_kwargs["log_with"] = args.report_to
        accelerator_log_kwargs["project_dir"] = args.output_dir

    accelerator = Accelerator(gradient_accumulation_steps=args.gradient_accumulation_steps, **accelerator_log_kwargs)

    logger.info(accelerator.state, main_process_only=False)
    if accelerator.is_local_main_process:
        datasets.utils.logging.set_verbosity_warning()
        transformers.utils.logging.set_verbosity_info()
    else:
        datasets.utils.logging.set_verbosity_error()
        transformers.utils.logging.set_verbosity_error()

    # If passed along, set the training seed now.
    # We set device_specific to True as we want different data augmentation per device.
    if args.seed is not None:
        set_seed(args.seed, device_specific=True)

    # Handle the repository creation
    if accelerator.is_main_process:
        if args.push_to_hub:
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

    # Load dataset
    # In distributed training, the load_dataset function guarantees that only one local process can concurrently
    # download the dataset.
    # TODO support datasets from local folders
    dataset = load_dataset(args.dataset_name, cache_dir=args.cache_dir, trust_remote_code=args.trust_remote_code)

    # Rename column names to standardized names (only "image" and "label" need to be present)
    if "pixel_values" in dataset["train"].column_names:
        dataset = dataset.rename_columns({"pixel_values": "image"})
    if "annotation" in dataset["train"].column_names:
        dataset = dataset.rename_columns({"annotation": "label"})

    # If we don't have a validation split, split off a percentage of train as validation.
    args.train_val_split = None if "validation" in dataset else args.train_val_split
    if isinstance(args.train_val_split, float) and args.train_val_split > 0.0:
        split = dataset["train"].train_test_split(args.train_val_split)
        dataset["train"] = split["train"]
        dataset["validation"] = split["test"]

    # Prepare label mappings.
    # We'll include these in the model's config to get human readable labels in the Inference API.
    if args.dataset_name == "scene_parse_150":
        repo_id = "huggingface/label-files"
        filename = "ade20k-id2label.json"
    else:
        repo_id = args.dataset_name
        filename = "id2label.json"
    id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset")))
    id2label = {int(k): v for k, v in id2label.items()}
    label2id = {v: k for k, v in id2label.items()}

    # Load pretrained model and image processor
    config = AutoConfig.from_pretrained(
        args.model_name_or_path, id2label=id2label, label2id=label2id, trust_remote_code=args.trust_remote_code
    )
    image_processor = AutoImageProcessor.from_pretrained(
        args.model_name_or_path, trust_remote_code=args.trust_remote_code, do_reduce_labels=args.do_reduce_labels
    )
    model = AutoModelForSemanticSegmentation.from_pretrained(
        args.model_name_or_path,
        config=config,
        trust_remote_code=args.trust_remote_code,
    )

    # Define transforms to be applied to each image and target.
    if "shortest_edge" in image_processor.size:
        # We instead set the target size as (shortest_edge, shortest_edge) to here to ensure all images are batchable.
        height, width = image_processor.size["shortest_edge"], image_processor.size["shortest_edge"]
    else:
        height, width = image_processor.size["height"], image_processor.size["width"]
    train_transforms = A.Compose(
        [
            A.Lambda(name="reduce_labels", mask=reduce_labels_transform if args.do_reduce_labels else None, p=1.0),
            # pad image with 255, because it is ignored by loss
            A.PadIfNeeded(min_height=height, min_width=width, border_mode=0, value=255, p=1.0),
            A.RandomCrop(height=height, width=width, p=1.0),
            A.HorizontalFlip(p=0.5),
            A.Normalize(mean=image_processor.image_mean, std=image_processor.image_std, max_pixel_value=255.0, p=1.0),
            ToTensorV2(),
        ]
    )
    val_transforms = A.Compose(
        [
            A.Lambda(name="reduce_labels", mask=reduce_labels_transform if args.do_reduce_labels else None, p=1.0),
            A.Resize(height=height, width=width, p=1.0),
            A.Normalize(mean=image_processor.image_mean, std=image_processor.image_std, max_pixel_value=255.0, p=1.0),
            ToTensorV2(),
        ]
    )

    def preprocess_batch(example_batch, transforms: A.Compose):
        pixel_values = []
        labels = []
        for image, target in zip(example_batch["image"], example_batch["label"]):
            transformed = transforms(image=np.array(image.convert("RGB")), mask=np.array(target))
            pixel_values.append(transformed["image"])
            labels.append(transformed["mask"])

        encoding = {}
        encoding["pixel_values"] = torch.stack(pixel_values).to(torch.float)
        encoding["labels"] = torch.stack(labels).to(torch.long)

        return encoding

    # Preprocess function for dataset should have only one input argument,
    # so we use partial to pass transforms
    preprocess_train_batch_fn = partial(preprocess_batch, transforms=train_transforms)
    preprocess_val_batch_fn = partial(preprocess_batch, transforms=val_transforms)

    with accelerator.main_process_first():
        train_dataset = dataset["train"].with_transform(preprocess_train_batch_fn)
        eval_dataset = dataset["validation"].with_transform(preprocess_val_batch_fn)

    train_dataloader = DataLoader(
        train_dataset, shuffle=True, collate_fn=default_data_collator, batch_size=args.per_device_train_batch_size
    )
    eval_dataloader = DataLoader(
        eval_dataset, collate_fn=default_data_collator, batch_size=args.per_device_eval_batch_size
    )

    # Optimizer
    optimizer = torch.optim.AdamW(
        list(model.parameters()),
        lr=args.learning_rate,
        betas=[args.adam_beta1, args.adam_beta2],
        eps=args.adam_epsilon,
    )

    # Figure out how many steps we should save the Accelerator states
    checkpointing_steps = args.checkpointing_steps
    if checkpointing_steps is not None and checkpointing_steps.isdigit():
        checkpointing_steps = int(checkpointing_steps)

    # Scheduler and math around the number of training steps.
    overrode_max_train_steps = False
    num_update_steps_per_epoch = math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)
    if args.max_train_steps is None:
        args.max_train_steps = args.num_train_epochs * num_update_steps_per_epoch
        overrode_max_train_steps = True

    lr_scheduler = get_scheduler(
        name=args.lr_scheduler_type,
        optimizer=optimizer,
        num_warmup_steps=args.num_warmup_steps * accelerator.num_processes,
        num_training_steps=args.max_train_steps
        if overrode_max_train_steps
        else args.max_train_steps * accelerator.num_processes,
    )

    # Prepare everything with our `accelerator`.
    model, optimizer, train_dataloader, eval_dataloader, lr_scheduler = accelerator.prepare(
        model, optimizer, train_dataloader, eval_dataloader, lr_scheduler
    )

    # We need to recalculate our total training steps as the size of the training dataloader may have changed.
    num_update_steps_per_epoch = math.ceil(len(train_dataloader) / args.gradient_accumulation_steps)
    if overrode_max_train_steps:
        args.max_train_steps = args.num_train_epochs * num_update_steps_per_epoch
    # Afterwards we recalculate our number of training epochs
    args.num_train_epochs = math.ceil(args.max_train_steps / num_update_steps_per_epoch)

    # Instantiate metric
    metric = evaluate.load("mean_iou", cache_dir=args.cache_dir)

    # We need to initialize the trackers we use, and also store our configuration.
    # The trackers initializes automatically on the main process.
    if args.with_tracking:
        experiment_config = vars(args)
        # TensorBoard cannot log Enums, need the raw value
        experiment_config["lr_scheduler_type"] = experiment_config["lr_scheduler_type"].value
        accelerator.init_trackers("semantic_segmentation_no_trainer", experiment_config)

    # Train!
    total_batch_size = args.per_device_train_batch_size * accelerator.num_processes * args.gradient_accumulation_steps

    logger.info("***** Running training *****")
    logger.info(f"  Num examples = {len(train_dataset)}")
    logger.info(f"  Num Epochs = {args.num_train_epochs}")
    logger.info(f"  Instantaneous batch size per device = {args.per_device_train_batch_size}")
    logger.info(f"  Total train batch size (w. parallel, distributed & accumulation) = {total_batch_size}")
    logger.info(f"  Gradient Accumulation steps = {args.gradient_accumulation_steps}")
    logger.info(f"  Total optimization steps = {args.max_train_steps}")
    # Only show the progress bar once on each machine.
    progress_bar = tqdm(range(args.max_train_steps), disable=not accelerator.is_local_main_process)
    completed_steps = 0
    starting_epoch = 0

    # Potentially load in the weights and states from a previous save
    if args.resume_from_checkpoint:
        if args.resume_from_checkpoint is not None or args.resume_from_checkpoint != "":
            checkpoint_path = args.resume_from_checkpoint
            path = os.path.basename(args.resume_from_checkpoint)
        else:
            # Get the most recent checkpoint
            dirs = [f.name for f in os.scandir(os.getcwd()) if f.is_dir()]
            dirs.sort(key=os.path.getctime)
            path = dirs[-1]  # Sorts folders by date modified, most recent checkpoint is the last
            checkpoint_path = path
            path = os.path.basename(checkpoint_path)

        accelerator.print(f"Resumed from checkpoint: {checkpoint_path}")
        accelerator.load_state(checkpoint_path)
        # Extract `epoch_{i}` or `step_{i}`
        training_difference = os.path.splitext(path)[0]

        if "epoch" in training_difference:
            starting_epoch = int(training_difference.replace("epoch_", "")) + 1
            resume_step = None
            completed_steps = starting_epoch * num_update_steps_per_epoch
        else:
            # need to multiply `gradient_accumulation_steps` to reflect real steps
            resume_step = int(training_difference.replace("step_", "")) * args.gradient_accumulation_steps
            starting_epoch = resume_step // len(train_dataloader)
            completed_steps = resume_step // args.gradient_accumulation_steps
            resume_step -= starting_epoch * len(train_dataloader)

    # update the progress_bar if load from checkpoint
    progress_bar.update(completed_steps)

    for epoch in range(starting_epoch, args.num_train_epochs):
        model.train()
        if args.with_tracking:
            total_loss = 0
        if args.resume_from_checkpoint and epoch == starting_epoch and resume_step is not None:
            # We skip the first `n` batches in the dataloader when resuming from a checkpoint
            active_dataloader = accelerator.skip_first_batches(train_dataloader, resume_step)
        else:
            active_dataloader = train_dataloader
        for step, batch in enumerate(active_dataloader):
            with accelerator.accumulate(model):
                outputs = model(**batch)
                loss = outputs.loss
                # We keep track of the loss at each epoch
                if args.with_tracking:
                    total_loss += loss.detach().float()
                accelerator.backward(loss)
                optimizer.step()
                lr_scheduler.step()
                optimizer.zero_grad()

            # Checks if the accelerator has performed an optimization step behind the scenes
            if accelerator.sync_gradients:
                progress_bar.update(1)
                completed_steps += 1

            if isinstance(checkpointing_steps, int):
                if completed_steps % checkpointing_steps == 0 and accelerator.sync_gradients:
                    output_dir = f"step_{completed_steps}"
                    if args.output_dir is not None:
                        output_dir = os.path.join(args.output_dir, output_dir)
                    accelerator.save_state(output_dir)

                    if args.push_to_hub and epoch < args.num_train_epochs - 1:
                        accelerator.wait_for_everyone()
                        unwrapped_model = accelerator.unwrap_model(model)
                        unwrapped_model.save_pretrained(
                            args.output_dir,
                            is_main_process=accelerator.is_main_process,
                            save_function=accelerator.save,
                        )
                        if accelerator.is_main_process:
                            image_processor.save_pretrained(args.output_dir)
                            api.upload_folder(
                                commit_message=f"Training in progress epoch {epoch}",
                                folder_path=args.output_dir,
                                repo_id=repo_id,
                                repo_type="model",
                                token=args.hub_token,
                            )

            if completed_steps >= args.max_train_steps:
                break

        logger.info("***** Running evaluation *****")
        model.eval()
        for step, batch in enumerate(tqdm(eval_dataloader, disable=not accelerator.is_local_main_process)):
            with torch.no_grad():
                outputs = model(**batch)

            upsampled_logits = torch.nn.functional.interpolate(
                outputs.logits, size=batch["labels"].shape[-2:], mode="bilinear", align_corners=False
            )
            predictions = upsampled_logits.argmax(dim=1)

            predictions, references = accelerator.gather_for_metrics((predictions, batch["labels"]))

            metric.add_batch(
                predictions=predictions,
                references=references,
            )

        eval_metrics = metric.compute(
            num_labels=len(id2label),
            ignore_index=255,
            reduce_labels=False,  # we've already reduced the labels before
        )
        logger.info(f"epoch {epoch}: {eval_metrics}")

        if args.with_tracking:
            accelerator.log(
                {
                    "mean_iou": eval_metrics["mean_iou"],
                    "mean_accuracy": eval_metrics["mean_accuracy"],
                    "overall_accuracy": eval_metrics["overall_accuracy"],
                    "train_loss": total_loss.item() / len(train_dataloader),
                    "epoch": epoch,
                    "step": completed_steps,
                },
                step=completed_steps,
            )

        if args.push_to_hub and epoch < args.num_train_epochs - 1:
            accelerator.wait_for_everyone()
            unwrapped_model = accelerator.unwrap_model(model)
            unwrapped_model.save_pretrained(
                args.output_dir, is_main_process=accelerator.is_main_process, save_function=accelerator.save
            )
            if accelerator.is_main_process:
                image_processor.save_pretrained(args.output_dir)
                api.upload_folder(
                    commit_message=f"Training in progress epoch {epoch}",
                    folder_path=args.output_dir,
                    repo_id=repo_id,
                    repo_type="model",
                    token=args.hub_token,
                )

        if args.checkpointing_steps == "epoch":
            output_dir = f"epoch_{epoch}"
            if args.output_dir is not None:
                output_dir = os.path.join(args.output_dir, output_dir)
            accelerator.save_state(output_dir)

    if args.output_dir is not None:
        accelerator.wait_for_everyone()
        unwrapped_model = accelerator.unwrap_model(model)
        unwrapped_model.save_pretrained(
            args.output_dir, is_main_process=accelerator.is_main_process, save_function=accelerator.save
        )
        if accelerator.is_main_process:
            image_processor.save_pretrained(args.output_dir)
            if args.push_to_hub:
                api.upload_folder(
                    commit_message="End of training",
                    folder_path=args.output_dir,
                    repo_id=repo_id,
                    repo_type="model",
                    token=args.hub_token,
                )

            all_results = {
                f"eval_{k}": v.tolist() if isinstance(v, np.ndarray) else v for k, v in eval_metrics.items()
            }
            with open(os.path.join(args.output_dir, "all_results.json"), "w") as f:
                json.dump(all_results, f, indent=2)

    accelerator.wait_for_everyone()
    accelerator.end_training()