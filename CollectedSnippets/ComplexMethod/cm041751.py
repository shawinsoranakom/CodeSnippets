def _check_extra_dependencies(
    model_args: "ModelArguments",
    finetuning_args: "FinetuningArguments",
    training_args: Optional["TrainingArguments"] = None,
) -> None:
    if model_args.use_kt:
        check_version("ktransformers", mandatory=True)

    if model_args.use_unsloth:
        check_version("unsloth", mandatory=True)

    if model_args.enable_liger_kernel:
        check_version("liger-kernel", mandatory=True)

    if model_args.mixture_of_depths is not None:
        check_version("mixture-of-depth>=1.1.6", mandatory=True)

    if model_args.infer_backend == EngineName.VLLM:
        check_version("vllm>=0.4.3,<=0.11.0")
        check_version("vllm", mandatory=True)
    elif model_args.infer_backend == EngineName.SGLANG:
        check_version("sglang>=0.4.5")
        check_version("sglang", mandatory=True)

    if finetuning_args.use_galore:
        check_version("galore_torch", mandatory=True)

    if finetuning_args.use_apollo:
        check_version("apollo_torch", mandatory=True)

    if finetuning_args.use_badam:
        check_version("badam>=1.2.1", mandatory=True)

    if finetuning_args.use_adam_mini:
        check_version("adam-mini", mandatory=True)

    if finetuning_args.use_swanlab:
        check_version("swanlab", mandatory=True)

    if finetuning_args.plot_loss:
        check_version("matplotlib", mandatory=True)

    if training_args is not None:
        if training_args.deepspeed:
            check_version("deepspeed", mandatory=True)

        if training_args.predict_with_generate:
            check_version("jieba", mandatory=True)
            check_version("nltk", mandatory=True)
            check_version("rouge_chinese", mandatory=True)