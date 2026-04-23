def run_sft(
    model_args: "ModelArguments",
    data_args: "DataArguments",
    training_args: "McaSeq2SeqTrainingArguments",
    finetuning_args: "FinetuningArguments",
    callbacks: Optional[list["TrainerCallback"]] = None,
):
    # align packing flags
    # TODO: FIX SequencePacking
    data_args.neat_packing = training_args.sequence_packing = data_args.neat_packing or training_args.sequence_packing
    data_args.packing = data_args.neat_packing or data_args.packing

    tokenizer_module = load_tokenizer(model_args)
    tokenizer = tokenizer_module["tokenizer"]
    template = get_template_and_fix_tokenizer(tokenizer, data_args)

    # dataset needs +1 then cut back due to MCA shift logic
    data_args.cutoff_len += 1
    dataset_module = get_dataset(template, model_args, data_args, training_args, stage="sft", **tokenizer_module)
    data_args.cutoff_len -= 1

    _check_model_support(model_args)
    model = AutoModel.from_pretrained(model_args.model_name_or_path, training_args)
    collator_model = _build_meta_hf_model_for_collator(model_args)

    # optional freezing for qwen_vl series
    _freeze_model_parameters(model, finetuning_args)

    pad_to_max = training_args.expert_model_parallel_size is not None and training_args.expert_model_parallel_size > 1
    data_collator = SFTDataCollatorWith4DAttentionMask(
        template=template,
        model=collator_model,
        padding="max_length" if pad_to_max else "longest",
        max_length=data_args.cutoff_len if pad_to_max else None,
        pad_to_multiple_of=64,
        label_pad_token_id=IGNORE_INDEX,
        **tokenizer_module,
    )
    data_collator = _data_collator_wrapper(data_collator)

    trainer = CustomMcaTrainer(
        model=model,
        args=training_args,
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=callbacks,
        **dataset_module,
    )

    if "processor" in tokenizer_module and tokenizer_module["processor"] is not None:
        trainer.add_callback(SaveProcessorCallback(tokenizer_module["processor"]))

    train_result = trainer.train(training_args.resume_from_checkpoint)
    trainer.save_model()
    trainer.log_metrics("train", train_result.metrics)
    trainer.save_metrics("train", train_result.metrics)
    trainer.save_state()
    if trainer.is_world_process_zero() and finetuning_args.plot_loss:
        keys = ["loss"]
        if isinstance(dataset_module.get("eval_dataset"), dict):
            keys += [f"eval_{key}_loss" for key in dataset_module["eval_dataset"].keys()]
        else:
            keys += ["eval_loss"]
        plot_loss(training_args.output_dir, keys=keys)