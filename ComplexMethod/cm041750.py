def _verify_model_args(
    model_args: "ModelArguments",
    data_args: "DataArguments",
    finetuning_args: "FinetuningArguments",
) -> None:
    if model_args.adapter_name_or_path is not None and finetuning_args.finetuning_type != "lora":
        raise ValueError("Adapter is only valid for the LoRA method.")

    if model_args.quantization_bit is not None:
        if finetuning_args.finetuning_type not in ["lora", "oft"]:
            raise ValueError("Quantization is only compatible with the LoRA or OFT method.")

        if finetuning_args.pissa_init:
            raise ValueError("Please use scripts/pissa_init.py to initialize PiSSA for a quantized model.")

        if model_args.resize_vocab:
            raise ValueError("Cannot resize embedding layers of a quantized model.")

        if model_args.adapter_name_or_path is not None and finetuning_args.create_new_adapter:
            raise ValueError("Cannot create new adapter upon a quantized model.")

        if model_args.adapter_name_or_path is not None and len(model_args.adapter_name_or_path) != 1:
            raise ValueError("Quantized model only accepts a single adapter. Merge them first.")