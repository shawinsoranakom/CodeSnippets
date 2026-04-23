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

    if training_args.should_log:
        # The default of training_args.log_level is passive, so we set log level at info here to have that default.
        transformers.utils.logging.set_verbosity_info()

    log_level = training_args.get_process_log_level()
    logger.setLevel(log_level)
    transformers.utils.logging.set_verbosity(log_level)
    transformers.utils.logging.enable_default_handler()
    transformers.utils.logging.enable_explicit_format()

    # Log on each process the small summary:
    logger.warning(
        f"Process rank: {training_args.local_process_index}, device: {training_args.device}, n_gpu: {training_args.n_gpu}, "
        + f"distributed training: {training_args.parallel_mode.value == 'distributed'}, 16-bits training: {training_args.fp16}"
    )
    logger.info(f"Training/evaluation parameters {training_args}")

    # Set seed before initializing model.
    set_seed(training_args.seed)

    # Initialize our dataset and prepare it for the audio classification task.
    raw_datasets = DatasetDict()
    raw_datasets["train"] = load_dataset(
        data_args.dataset_name,
        data_args.dataset_config_name,
        split=data_args.train_split_name,
        token=model_args.token,
        trust_remote_code=model_args.trust_remote_code,
    )
    raw_datasets["eval"] = load_dataset(
        data_args.dataset_name,
        data_args.dataset_config_name,
        split=data_args.eval_split_name,
        token=model_args.token,
        trust_remote_code=model_args.trust_remote_code,
    )

    if data_args.audio_column_name not in raw_datasets["train"].column_names:
        raise ValueError(
            f"--audio_column_name {data_args.audio_column_name} not found in dataset '{data_args.dataset_name}'. "
            "Make sure to set `--audio_column_name` to the correct audio column - one of "
            f"{', '.join(raw_datasets['train'].column_names)}."
        )

    if data_args.label_column_name not in raw_datasets["train"].column_names:
        raise ValueError(
            f"--label_column_name {data_args.label_column_name} not found in dataset '{data_args.dataset_name}'. "
            "Make sure to set `--label_column_name` to the correct text column - one of "
            f"{', '.join(raw_datasets['train'].column_names)}."
        )

    # Setting `return_attention_mask=True` is the way to get a correctly masked mean-pooling over
    # transformer outputs in the classifier, but it doesn't always lead to better accuracy
    feature_extractor = AutoFeatureExtractor.from_pretrained(
        model_args.feature_extractor_name or model_args.model_name_or_path,
        return_attention_mask=model_args.attention_mask,
        cache_dir=model_args.cache_dir,
        revision=model_args.model_revision,
        token=model_args.token,
        trust_remote_code=model_args.trust_remote_code,
    )

    # `datasets` takes care of automatically loading and resampling the audio,
    # so we just need to set the correct target sampling rate.
    raw_datasets = raw_datasets.cast_column(
        data_args.audio_column_name, datasets.features.Audio(sampling_rate=feature_extractor.sampling_rate)
    )

    model_input_name = feature_extractor.model_input_names[0]

    def train_transforms(batch):
        """Apply train_transforms across a batch."""
        subsampled_wavs = []
        for audio in batch[data_args.audio_column_name]:
            wav = random_subsample(
                audio["array"], max_length=data_args.max_length_seconds, sample_rate=feature_extractor.sampling_rate
            )
            subsampled_wavs.append(wav)
        inputs = feature_extractor(subsampled_wavs, sampling_rate=feature_extractor.sampling_rate)
        output_batch = {model_input_name: inputs.get(model_input_name)}
        output_batch["labels"] = list(batch[data_args.label_column_name])

        return output_batch

    def val_transforms(batch):
        """Apply val_transforms across a batch."""
        wavs = [audio["array"] for audio in batch[data_args.audio_column_name]]
        inputs = feature_extractor(wavs, sampling_rate=feature_extractor.sampling_rate)
        output_batch = {model_input_name: inputs.get(model_input_name)}
        output_batch["labels"] = list(batch[data_args.label_column_name])

        return output_batch

    # Prepare label mappings.
    # We'll include these in the model's config to get human readable labels in the Inference API.
    labels = raw_datasets["train"].features[data_args.label_column_name].names
    label2id, id2label = {}, {}
    for i, label in enumerate(labels):
        label2id[label] = str(i)
        id2label[str(i)] = label

    # Load the accuracy metric from the datasets package
    metric = evaluate.load("accuracy", cache_dir=model_args.cache_dir)

    # Define our compute_metrics function. It takes an `EvalPrediction` object (a namedtuple with
    # `predictions` and `label_ids` fields) and has to return a dictionary string to float.
    def compute_metrics(eval_pred):
        """Computes accuracy on a batch of predictions"""
        predictions = np.argmax(eval_pred.predictions, axis=1)
        return metric.compute(predictions=predictions, references=eval_pred.label_ids)

    config = AutoConfig.from_pretrained(
        model_args.config_name or model_args.model_name_or_path,
        num_labels=len(labels),
        label2id=label2id,
        id2label=id2label,
        finetuning_task="audio-classification",
        cache_dir=model_args.cache_dir,
        revision=model_args.model_revision,
        token=model_args.token,
        trust_remote_code=model_args.trust_remote_code,
    )
    model = AutoModelForAudioClassification.from_pretrained(
        model_args.model_name_or_path,
        from_tf=bool(".ckpt" in model_args.model_name_or_path),
        config=config,
        cache_dir=model_args.cache_dir,
        revision=model_args.model_revision,
        token=model_args.token,
        trust_remote_code=model_args.trust_remote_code,
        ignore_mismatched_sizes=model_args.ignore_mismatched_sizes,
    )

    # freeze the convolutional waveform encoder
    if model_args.freeze_feature_encoder:
        model.freeze_feature_encoder()

    if training_args.do_train:
        if data_args.max_train_samples is not None:
            raw_datasets["train"] = (
                raw_datasets["train"].shuffle(seed=training_args.seed).select(range(data_args.max_train_samples))
            )
        # Set the training transforms
        raw_datasets["train"].set_transform(train_transforms, output_all_columns=False)

    if training_args.do_eval:
        if data_args.max_eval_samples is not None:
            raw_datasets["eval"] = (
                raw_datasets["eval"].shuffle(seed=training_args.seed).select(range(data_args.max_eval_samples))
            )
        # Set the validation transforms
        raw_datasets["eval"].set_transform(val_transforms, output_all_columns=False)

    # Initialize our trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=raw_datasets["train"] if training_args.do_train else None,
        eval_dataset=raw_datasets["eval"] if training_args.do_eval else None,
        compute_metrics=compute_metrics,
        processing_class=feature_extractor,
    )

    # Training
    if training_args.do_train:
        checkpoint = None
        if training_args.resume_from_checkpoint is not None:
            checkpoint = training_args.resume_from_checkpoint
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model()
        trainer.log_metrics("train", train_result.metrics)
        trainer.save_metrics("train", train_result.metrics)
        trainer.save_state()

    # Evaluation
    if training_args.do_eval:
        metrics = trainer.evaluate()
        trainer.log_metrics("eval", metrics)
        trainer.save_metrics("eval", metrics)

    # Write model card and (optionally) push to hub
    kwargs = {
        "finetuned_from": model_args.model_name_or_path,
        "tasks": "audio-classification",
        "dataset": data_args.dataset_name,
        "tags": ["audio-classification"],
    }
    if training_args.push_to_hub:
        trainer.push_to_hub(**kwargs)
    else:
        trainer.create_model_card(**kwargs)