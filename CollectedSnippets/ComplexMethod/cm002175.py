def main():
    # See all possible arguments in https://huggingface.co/docs/transformers/main_classes/trainer#transformers.TrainingArguments
    # or by passing the --help flag to this script.

    parser = HfArgumentParser([Arguments, TrainingArguments])
    if len(sys.argv) == 2 and sys.argv[1].endswith(".json"):
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        args, training_args = parser.parse_json_file(json_file=os.path.abspath(sys.argv[1]))
    else:
        args, training_args = parser.parse_args_into_dataclasses()

    # Set default training arguments for instance segmentation
    training_args.eval_do_concat_batches = False
    training_args.batch_eval_metrics = True
    training_args.remove_unused_columns = False

    # Setup logging and log on each process the small summary:
    setup_logging(training_args)
    logger.warning(
        f"Process rank: {training_args.local_process_index}, device: {training_args.device}, n_gpu: {training_args.n_gpu}, "
        + f"distributed training: {training_args.parallel_mode.value == 'distributed'}, 16-bits training: {training_args.fp16}"
    )
    logger.info(f"Training/evaluation parameters {training_args}")

    # Load last checkpoint from output_dir if it exists (and we are not overwriting it)
    checkpoint = find_last_checkpoint(training_args)

    # ------------------------------------------------------------------------------------------------
    # Load dataset, prepare splits
    # ------------------------------------------------------------------------------------------------

    dataset = load_dataset(args.dataset_name, trust_remote_code=args.trust_remote_code)

    # We need to specify the label2id mapping for the model
    # it is a mapping from semantic class name to class index.
    # In case your dataset does not provide it, you can create it manually:
    # label2id = {"background": 0, "cat": 1, "dog": 2}
    label2id = dataset["train"][0]["semantic_class_to_id"]

    if args.do_reduce_labels:
        label2id = {name: idx for name, idx in label2id.items() if idx != 0}  # remove background class
        label2id = {name: idx - 1 for name, idx in label2id.items()}  # shift class indices by -1

    id2label = {v: k for k, v in label2id.items()}

    # ------------------------------------------------------------------------------------------------
    # Load pretrained config, model and image processor
    # ------------------------------------------------------------------------------------------------
    model = AutoModelForUniversalSegmentation.from_pretrained(
        args.model_name_or_path,
        label2id=label2id,
        id2label=id2label,
        ignore_mismatched_sizes=True,
        token=args.token,
    )

    image_processor = AutoImageProcessor.from_pretrained(
        args.model_name_or_path,
        do_resize=True,
        size={"height": args.image_height, "width": args.image_width},
        do_reduce_labels=args.do_reduce_labels,
        reduce_labels=args.do_reduce_labels,  # TODO: remove when mask2former support `do_reduce_labels`
        token=args.token,
    )

    # ------------------------------------------------------------------------------------------------
    # Define image augmentations and dataset transforms
    # ------------------------------------------------------------------------------------------------
    train_augment_and_transform = A.Compose(
        [
            A.HorizontalFlip(p=0.5),
            A.RandomBrightnessContrast(p=0.5),
            A.HueSaturationValue(p=0.1),
        ],
    )
    validation_transform = A.Compose(
        [A.NoOp()],
    )

    # Make transform functions for batch and apply for dataset splits
    train_transform_batch = partial(
        augment_and_transform_batch, transform=train_augment_and_transform, image_processor=image_processor
    )
    validation_transform_batch = partial(
        augment_and_transform_batch, transform=validation_transform, image_processor=image_processor
    )

    dataset["train"] = dataset["train"].with_transform(train_transform_batch)
    dataset["validation"] = dataset["validation"].with_transform(validation_transform_batch)

    # ------------------------------------------------------------------------------------------------
    # Model training and evaluation with Trainer API
    # ------------------------------------------------------------------------------------------------

    compute_metrics = Evaluator(image_processor=image_processor, id2label=id2label, threshold=0.0)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=dataset["train"] if training_args.do_train else None,
        eval_dataset=dataset["validation"] if training_args.do_eval else None,
        processing_class=image_processor,
        data_collator=collate_fn,
        compute_metrics=compute_metrics,
    )

    # Training
    if training_args.do_train:
        train_result = trainer.train(resume_from_checkpoint=checkpoint)
        trainer.save_model()
        trainer.log_metrics("train", train_result.metrics)
        trainer.save_metrics("train", train_result.metrics)
        trainer.save_state()

    # Final evaluation
    if training_args.do_eval:
        metrics = trainer.evaluate(eval_dataset=dataset["validation"], metric_key_prefix="test")
        trainer.log_metrics("test", metrics)
        trainer.save_metrics("test", metrics)

    # Write model card and (optionally) push to hub
    kwargs = {
        "finetuned_from": args.model_name_or_path,
        "dataset": args.dataset_name,
        "tags": ["image-segmentation", "instance-segmentation", "vision"],
    }
    if training_args.push_to_hub:
        trainer.push_to_hub(**kwargs)
    else:
        trainer.create_model_card(**kwargs)