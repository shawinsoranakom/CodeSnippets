def main():
    # See all possible arguments in src/transformers/training_args.py
    # or by passing the --help flag to this script.
    # We now keep distinct sets of args, for a cleaner separation of concerns.

    parser = HfArgumentParser((ModelArguments, DataTrainingArguments, TrainingArguments))
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        model_args, data_args, training_args = parser.parse_json_file(json_file=os.path.abspath(sys.argv[1]))
    else:
        model_args, data_args, training_args = parser.parse_args_into_dataclasses()

    # Setup logging
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    logger.setLevel(logging.INFO if is_main_process(training_args.local_process_index) else logging.WARN)

    # Log on each process the small summary:
    logger.warning(
        f"Process rank: {training_args.local_process_index}, device: {training_args.device}, n_gpu: {training_args.n_gpu}, "
        f"distributed training: {training_args.parallel_mode.value == 'distributed'}, 16-bits training: {training_args.fp16}"
    )
    # Set the verbosity to info of the Transformers logger (on main process only):
    if is_main_process(training_args.local_process_index):
        transformers.utils.logging.set_verbosity_info()
    logger.info("Training/evaluation parameters %s", training_args)

    # Set seed before initializing model.
    set_seed(training_args.seed)

    # 1. First, let's load the dataset
    raw_datasets = DatasetDict()

    if training_args.do_train:
        raw_datasets["train"] = load_dataset(
            data_args.dataset_name,
            data_args.dataset_config_name,
            split=data_args.train_split_name,
            token=data_args.token,
            trust_remote_code=data_args.trust_remote_code,
        )

        if data_args.audio_column_name not in raw_datasets["train"].column_names:
            raise ValueError(
                f"--audio_column_name '{data_args.audio_column_name}' not found in dataset '{data_args.dataset_name}'."
                " Make sure to set `--audio_column_name` to the correct audio column - one of"
                f" {', '.join(raw_datasets['train'].column_names)}."
            )

        if data_args.text_column_name not in raw_datasets["train"].column_names:
            raise ValueError(
                f"--text_column_name {data_args.text_column_name} not found in dataset '{data_args.dataset_name}'. "
                "Make sure to set `--text_column_name` to the correct text column - one of "
                f"{', '.join(raw_datasets['train'].column_names)}."
            )

        if data_args.max_train_samples is not None:
            raw_datasets["train"] = raw_datasets["train"].select(range(data_args.max_train_samples))

    if training_args.do_eval:
        raw_datasets["eval"] = load_dataset(
            data_args.dataset_name,
            data_args.dataset_config_name,
            split=data_args.eval_split_name,
            token=data_args.token,
            trust_remote_code=data_args.trust_remote_code,
        )

        if data_args.max_eval_samples is not None:
            raw_datasets["eval"] = raw_datasets["eval"].select(range(data_args.max_eval_samples))

    # 2. We remove some special characters from the datasets
    # that make training complicated and do not help in transcribing the speech
    # E.g. characters, such as `,` and `.` do not really have an acoustic characteristic
    # that could be easily picked up by the model
    chars_to_ignore_regex = (
        f"[{''.join(data_args.chars_to_ignore)}]" if data_args.chars_to_ignore is not None else None
    )
    text_column_name = data_args.text_column_name

    def remove_special_characters(batch):
        if chars_to_ignore_regex is not None:
            batch["target_text"] = re.sub(chars_to_ignore_regex, "", batch[text_column_name]).lower() + " "
        else:
            batch["target_text"] = batch[text_column_name].lower() + " "
        return batch

    with training_args.main_process_first(desc="dataset map special characters removal"):
        raw_datasets = raw_datasets.map(
            remove_special_characters,
            remove_columns=[text_column_name],
            desc="remove special characters from datasets",
        )

    # save special tokens for tokenizer
    word_delimiter_token = data_args.word_delimiter_token
    unk_token = data_args.unk_token
    pad_token = data_args.pad_token

    # 3. Next, let's load the config as we might need it to create
    # the tokenizer
    # load config
    config = AutoConfig.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        token=data_args.token,
        trust_remote_code=data_args.trust_remote_code,
    )

    # 4. Next, if no tokenizer file is defined,
    # we create the vocabulary of the model by extracting all unique characters from
    # the training and evaluation datasets
    # We need to make sure that only first rank saves vocabulary
    # make sure all processes wait until vocab is created
    tokenizer_name_or_path = model_args.tokenizer_name_or_path
    tokenizer_kwargs = {}
    if tokenizer_name_or_path is None:
        # save vocab in training output dir
        tokenizer_name_or_path = training_args.output_dir

        vocab_file = os.path.join(tokenizer_name_or_path, "vocab.json")

        with training_args.main_process_first():
            if os.path.isfile(vocab_file):
                try:
                    os.remove(vocab_file)
                except OSError:
                    # in shared file-systems it might be the case that
                    # two processes try to delete the vocab file at the some time
                    pass

        with training_args.main_process_first(desc="dataset map vocabulary creation"):
            if not os.path.isfile(vocab_file):
                os.makedirs(tokenizer_name_or_path, exist_ok=True)
                vocab_dict = create_vocabulary_from_data(
                    raw_datasets,
                    word_delimiter_token=word_delimiter_token,
                    unk_token=unk_token,
                    pad_token=pad_token,
                )

                # save vocab dict to be loaded into tokenizer
                with open(vocab_file, "w") as file:
                    json.dump(vocab_dict, file)

        tokenizer_kwargs = {
            "config": config,
            "tokenizer_type": config.model_type,
            "unk_token": unk_token,
            "pad_token": pad_token,
            "word_delimiter_token": word_delimiter_token,
        }

    # 5. Now we can instantiate the feature extractor, tokenizer and model
    # Note for distributed training, the .from_pretrained methods guarantee that only
    # one local process can concurrently download model & vocab.

    # load feature_extractor and tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        tokenizer_name_or_path,
        token=data_args.token,
        trust_remote_code=data_args.trust_remote_code,
        **tokenizer_kwargs,
    )
    feature_extractor = AutoFeatureExtractor.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        token=data_args.token,
        trust_remote_code=data_args.trust_remote_code,
    )

    # adapt config
    config.update(
        {
            "feat_proj_dropout": model_args.feat_proj_dropout,
            "attention_dropout": model_args.attention_dropout,
            "hidden_dropout": model_args.hidden_dropout,
            "final_dropout": model_args.final_dropout,
            "mask_time_prob": model_args.mask_time_prob,
            "mask_time_length": model_args.mask_time_length,
            "mask_feature_prob": model_args.mask_feature_prob,
            "mask_feature_length": model_args.mask_feature_length,
            "gradient_checkpointing": training_args.gradient_checkpointing,
            "layerdrop": model_args.layerdrop,
            "ctc_loss_reduction": model_args.ctc_loss_reduction,
            "ctc_zero_infinity": model_args.ctc_zero_infinity,
            "pad_token_id": tokenizer.pad_token_id,
            "vocab_size": len(tokenizer),
            "activation_dropout": model_args.activation_dropout,
            "add_adapter": model_args.add_adapter,
        }
    )

    # create model
    model = AutoModelForCTC.from_pretrained(
        model_args.model_name_or_path,
        cache_dir=model_args.cache_dir,
        config=config,
        token=data_args.token,
        trust_remote_code=data_args.trust_remote_code,
    )

    # freeze encoder
    if model_args.freeze_feature_encoder:
        model.freeze_feature_encoder()

    # 6. Now we preprocess the datasets including loading the audio, resampling and normalization
    # Thankfully, `datasets` takes care of automatically loading and resampling the audio,
    # so that we just need to set the correct target sampling rate and normalize the input
    # via the `feature_extractor`

    # make sure that dataset decodes audio with correct sampling rate
    dataset_sampling_rate = next(iter(raw_datasets.values())).features[data_args.audio_column_name].sampling_rate
    if dataset_sampling_rate != feature_extractor.sampling_rate:
        raw_datasets = raw_datasets.cast_column(
            data_args.audio_column_name,
            datasets.features.Audio(sampling_rate=feature_extractor.sampling_rate),
        )

    # derive max & min input length for sample rate & max duration
    max_input_length = data_args.max_duration_in_seconds * feature_extractor.sampling_rate
    min_input_length = data_args.min_duration_in_seconds * feature_extractor.sampling_rate
    audio_column_name = data_args.audio_column_name
    num_workers = data_args.preprocessing_num_workers
    feature_extractor_input_name = feature_extractor.model_input_names[0]

    # `phoneme_language` is only relevant if the model is fine-tuned on phoneme classification
    phoneme_language = data_args.phoneme_language

    # Preprocessing the datasets.
    # We need to read the audio files as arrays and tokenize the targets.
    def prepare_dataset(batch):
        # load audio
        sample = batch[audio_column_name]

        inputs = feature_extractor(sample["array"], sampling_rate=sample["sampling_rate"])
        batch[feature_extractor_input_name] = getattr(inputs, feature_extractor_input_name)[0]
        # take length of raw audio waveform
        batch["input_length"] = len(sample["array"].squeeze())

        # encode targets
        additional_kwargs = {}
        if phoneme_language is not None:
            additional_kwargs["phonemizer_lang"] = phoneme_language

        batch["labels"] = tokenizer(batch["target_text"], **additional_kwargs).input_ids
        return batch

    with training_args.main_process_first(desc="dataset map preprocessing"):
        vectorized_datasets = raw_datasets.map(
            prepare_dataset,
            remove_columns=next(iter(raw_datasets.values())).column_names,
            num_proc=num_workers,
            desc="preprocess datasets",
        )

        def is_audio_in_length_range(length):
            return length > min_input_length and length < max_input_length

        # filter data that is shorter than min_input_length
        vectorized_datasets = vectorized_datasets.filter(
            is_audio_in_length_range,
            num_proc=num_workers,
            input_columns=["input_length"],
        )

    # 7. Next, we can prepare the training.
    # Let's use word error rate (WER) as our evaluation metric,
    # instantiate a data collator and the trainer

    # Define evaluation metrics during training, *i.e.* word error rate, character error rate
    eval_metrics = {metric: evaluate.load(metric, cache_dir=model_args.cache_dir) for metric in data_args.eval_metrics}

    # for large datasets it is advised to run the preprocessing on a
    # single machine first with ``args.preprocessing_only`` since there will mostly likely
    # be a timeout when running the script in distributed mode.
    # In a second step ``args.preprocessing_only`` can then be set to `False` to load the
    # cached dataset
    if data_args.preprocessing_only:
        logger.info(f"Data preprocessing finished. Files cached at {vectorized_datasets.cache_files}")
        return

    # For languages like Chinese with large vocabulary size, we need to discard logits
    # and only keep the argmax, otherwise we run out of memory during evaluation.
    def preprocess_logits_for_metrics(logits, labels):
        pred_ids = torch.argmax(logits, dim=-1)
        return pred_ids, labels

    def compute_metrics(pred):
        pred_ids = pred.predictions[0]
        pred.label_ids[pred.label_ids == -100] = tokenizer.pad_token_id

        pred_str = tokenizer.batch_decode(pred_ids)
        # we do not want to group tokens when computing the metrics
        label_str = tokenizer.batch_decode(pred.label_ids, group_tokens=False)

        metrics = {k: v.compute(predictions=pred_str, references=label_str) for k, v in eval_metrics.items()}

        return metrics

    # Now save everything to be able to create a single processor later
    # make sure all processes wait until data is saved
    with training_args.main_process_first():
        # only the main process saves them
        if is_main_process(training_args.local_process_index):
            # save feature extractor, tokenizer and config
            feature_extractor.save_pretrained(training_args.output_dir)
            tokenizer.save_pretrained(training_args.output_dir)
            config.save_pretrained(training_args.output_dir)

    processor = AutoProcessor.from_pretrained(training_args.output_dir)

    # Instantiate custom data collator
    data_collator = DataCollatorCTCWithPadding(
        processor=processor, feature_extractor_input_name=feature_extractor_input_name
    )

    # Initialize Trainer
    trainer = Trainer(
        model=model,
        data_collator=data_collator,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=vectorized_datasets["train"] if training_args.do_train else None,
        eval_dataset=vectorized_datasets["eval"] if training_args.do_eval else None,
        processing_class=processor,
        preprocess_logits_for_metrics=preprocess_logits_for_metrics,
    )

    # 8. Finally, we can start training

    # Training
    if training_args.do_train:
        # use last checkpoint if exist
        if os.path.isdir(model_args.model_name_or_path):
            checkpoint = model_args.model_name_or_path
        else:
            checkpoint = None

        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model()

        metrics = train_result.metrics
        max_train_samples = (
            data_args.max_train_samples
            if data_args.max_train_samples is not None
            else len(vectorized_datasets["train"])
        )
        metrics["train_samples"] = min(max_train_samples, len(vectorized_datasets["train"]))

        trainer.log_metrics("train", metrics)
        trainer.save_metrics("train", metrics)
        trainer.save_state()

    # Evaluation
    results = {}
    if training_args.do_eval:
        logger.info("*** Evaluate ***")
        metrics = trainer.evaluate()
        max_eval_samples = (
            data_args.max_eval_samples if data_args.max_eval_samples is not None else len(vectorized_datasets["eval"])
        )
        metrics["eval_samples"] = min(max_eval_samples, len(vectorized_datasets["eval"]))

        trainer.log_metrics("eval", metrics)
        trainer.save_metrics("eval", metrics)

    # Write model card and (optionally) push to hub
    config_name = data_args.dataset_config_name if data_args.dataset_config_name is not None else "na"
    kwargs = {
        "finetuned_from": model_args.model_name_or_path,
        "tasks": "automatic-speech-recognition",
        "tags": ["automatic-speech-recognition", data_args.dataset_name],
        "dataset_args": (
            f"Config: {config_name}, Training split: {data_args.train_split_name}, Eval split:"
            f" {data_args.eval_split_name}"
        ),
        "dataset": f"{data_args.dataset_name.upper()} - {config_name.upper()}",
    }
    if "common_voice" in data_args.dataset_name:
        kwargs["language"] = config_name

    if training_args.push_to_hub:
        trainer.push_to_hub(**kwargs)
    else:
        trainer.create_model_card(**kwargs)

    return results