def merge_and_export_model(args: InputArgument = None):
    model_args, _, _, _ = get_args(args)

    export_config = model_args.peft_config
    if export_config is None:
        raise ValueError("Please specify peft_config to merge and export model.")

    export_dir = export_config.get("export_dir")
    if export_dir is None:
        raise ValueError("Please specify export_dir.")

    export_size = export_config.get("export_size", 5)
    export_hub_model_id = export_config.get("export_hub_model_id")
    infer_dtype = export_config.get("infer_dtype", "auto")
    export_legacy_format = export_config.get("export_legacy_format", False)

    adapters = None
    if export_config.get("name") == "lora":
        adapters = export_config.get("adapter_name_or_path")
    else:
        raise ValueError("Currently merge and export model function is only supported for lora.")

    if adapters is None:
        raise ValueError("Please set adapter_name_or_path to merge adapters into base model.")

    logger.info_rank0("Loading model for export...")
    model_engine = ModelEngine(model_args, is_train=False)
    model = model_engine.model
    tokenizer = model_engine.processor

    if infer_dtype == "auto":
        if model.config.torch_dtype == torch.float32 and torch.cuda.is_bf16_supported():
            model = model.to(torch.bfloat16)
            logger.info_rank0("Converted model to bfloat16.")
    else:
        target_dtype = getattr(torch, infer_dtype)
        model = model.to(target_dtype)
        logger.info_rank0(f"Converted model to {infer_dtype}.")

    logger.info_rank0(f"Exporting model to {export_dir}...")
    model.save_pretrained(
        export_dir,
        max_shard_size=f"{export_size}GB",
        safe_serialization=not export_legacy_format,
    )
    if tokenizer is not None:
        try:
            if hasattr(tokenizer, "padding_side"):
                tokenizer.padding_side = "left"
            tokenizer.save_pretrained(export_dir)
        except Exception as e:
            logger.warning(f"Failed to save tokenizer: {e}")

    if export_hub_model_id:
        logger.info_rank0(f"Pushing to hub: {export_hub_model_id}...")
        model.push_to_hub(export_hub_model_id)
        if tokenizer is not None:
            tokenizer.push_to_hub(export_hub_model_id)

    logger.info_rank0("Model exported successfully.")