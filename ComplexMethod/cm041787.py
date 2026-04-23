def run_dpo(
    model_args: "ModelArguments",
    data_args: "DataArguments",
    training_args: "McaSeq2SeqTrainingArguments",
    finetuning_args: "FinetuningArguments",
    callbacks: Optional[list["TrainerCallback"]] = None,
):
    tokenizer_module = load_tokenizer(model_args)
    tokenizer = tokenizer_module["tokenizer"]
    template = get_template_and_fix_tokenizer(tokenizer, data_args)

    _check_model_support(model_args)
    model = AutoModel.from_pretrained(model_args.model_name_or_path, training_args)
    collator_model = _build_meta_hf_model_for_collator(model_args)

    _freeze_model_parameters(model, finetuning_args)

    if finetuning_args.use_ref_model:
        ref_config = AutoConfig.from_pretrained(model_args.model_name_or_path, training_args)
        ref_model = AutoModel.from_config(ref_config)
        ref_model.load_state_dict(model.state_dict())
    else:
        ref_model = None

    # dataset needs +1 then cut back due to MCA shift logic
    data_args.cutoff_len += 1
    dataset_module = get_dataset(template, model_args, data_args, training_args, stage="rm", **tokenizer_module)
    data_args.cutoff_len -= 1

    pad_to_max = training_args.expert_model_parallel_size is not None and training_args.expert_model_parallel_size > 1
    dpo_config = DPOConfig(
        beta=finetuning_args.pref_beta,
        pref_loss=finetuning_args.pref_loss,
        label_smoothing=finetuning_args.dpo_label_smoothing,
    )
    data_collator = PairwiseDataCollatorWithPadding(
        template=template,
        model=collator_model,
        pad_to_multiple_of=64,
        padding="max_length" if pad_to_max else "longest",
        max_length=data_args.cutoff_len if pad_to_max else None,
        label_pad_token_id=IGNORE_INDEX,
        **tokenizer_module,
    )
    data_collator = _data_collator_wrapper(data_collator)

    trainer = McaDPOTrainer(
        model=model,
        ref_model=ref_model,
        args=training_args,
        train_config=dpo_config,
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=callbacks,
        **dataset_module,
    )

    if "processor" in tokenizer_module and tokenizer_module["processor"] is not None:
        trainer.add_callback(SaveProcessorCallback(tokenizer_module["processor"]))

    train_result = trainer.train(training_args.resume_from_checkpoint)
    trainer.save_model()
    if finetuning_args.include_effective_tokens_per_second:
        train_result.metrics["effective_tokens_per_sec"] = calculate_tps(
            dataset_module["train_dataset"], train_result.metrics, stage="rm"
        )

    trainer.log_metrics("train", train_result.metrics)
    trainer.save_metrics("train", train_result.metrics)
    trainer.save_state()
    if trainer.is_world_process_zero() and finetuning_args.plot_loss:
        keys = ["loss", "rewards/accuracies"]
        if isinstance(dataset_module.get("eval_dataset"), dict):
            keys += [f"eval_{key}_loss" for key in dataset_module["eval_dataset"].keys()]
        else:
            keys += ["eval_loss"]

        plot_loss(training_args.output_dir, keys=keys)