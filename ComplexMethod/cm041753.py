def get_infer_args(args: dict[str, Any] | list[str] | None = None) -> _INFER_CLS:
    model_args, data_args, finetuning_args, generating_args = _parse_infer_args(args)

    # Setup logging
    _set_transformers_logging()

    # Check arguments
    if model_args.infer_backend == "vllm":
        if finetuning_args.stage != "sft":
            raise ValueError("vLLM engine only supports auto-regressive models.")

        if model_args.quantization_bit is not None:
            raise ValueError("vLLM engine does not support bnb quantization (GPTQ and AWQ are supported).")

        if model_args.rope_scaling is not None:
            raise ValueError("vLLM engine does not support RoPE scaling.")

        if model_args.adapter_name_or_path is not None and len(model_args.adapter_name_or_path) != 1:
            raise ValueError("vLLM only accepts a single adapter. Merge them first.")

    _set_env_vars()
    _verify_model_args(model_args, data_args, finetuning_args)
    _check_extra_dependencies(model_args, finetuning_args)

    # Post-process model arguments
    if model_args.export_dir is not None and model_args.export_device == "cpu":
        model_args.device_map = {"": torch.device("cpu")}
        if data_args.cutoff_len != DataArguments().cutoff_len:  # override cutoff_len if it is not default
            model_args.model_max_length = data_args.cutoff_len
    else:
        model_args.device_map = "auto"

    return model_args, data_args, finetuning_args, generating_args