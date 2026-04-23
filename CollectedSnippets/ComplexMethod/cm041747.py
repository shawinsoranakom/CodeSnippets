def save_model(
    lang: str,
    model_name: str,
    model_path: str,
    finetuning_type: str,
    checkpoint_path: str | list[str],
    template: str,
    export_size: int,
    export_quantization_bit: str,
    export_quantization_dataset: str,
    export_device: str,
    export_legacy_format: bool,
    export_dir: str,
    export_hub_model_id: str,
    extra_args: str,
) -> Generator[str, None, None]:
    user_config = load_config()
    error = ""
    if not model_name:
        error = ALERTS["err_no_model"][lang]
    elif not model_path:
        error = ALERTS["err_no_path"][lang]
    elif not export_dir:
        error = ALERTS["err_no_export_dir"][lang]
    elif export_quantization_bit in GPTQ_BITS and not export_quantization_dataset:
        error = ALERTS["err_no_dataset"][lang]
    elif export_quantization_bit not in GPTQ_BITS and not checkpoint_path:
        error = ALERTS["err_no_adapter"][lang]
    elif export_quantization_bit in GPTQ_BITS and checkpoint_path and isinstance(checkpoint_path, list):
        error = ALERTS["err_gptq_lora"][lang]

    try:
        json.loads(extra_args)
    except json.JSONDecodeError:
        error = ALERTS["err_json_schema"][lang]

    if error:
        gr.Warning(error)
        yield error
        return

    args = dict(
        model_name_or_path=model_path,
        cache_dir=user_config.get("cache_dir", None),
        finetuning_type=finetuning_type,
        template=template,
        export_dir=export_dir,
        export_hub_model_id=export_hub_model_id or None,
        export_size=export_size,
        export_quantization_bit=int(export_quantization_bit) if export_quantization_bit in GPTQ_BITS else None,
        export_quantization_dataset=export_quantization_dataset,
        export_device=export_device,
        export_legacy_format=export_legacy_format,
        trust_remote_code=True,
    )
    args.update(json.loads(extra_args))

    if checkpoint_path:
        if finetuning_type in PEFT_METHODS:  # list
            args["adapter_name_or_path"] = ",".join(
                [get_save_dir(model_name, finetuning_type, adapter) for adapter in checkpoint_path]
            )
        else:  # str
            args["model_name_or_path"] = get_save_dir(model_name, finetuning_type, checkpoint_path)

    yield ALERTS["info_exporting"][lang]
    export_model(args)
    torch_gc()
    yield ALERTS["info_exported"][lang]