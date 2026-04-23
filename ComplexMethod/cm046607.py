def build_config_builder(recipe: dict[str, Any]):
    _apply_data_designer_image_context_patch()
    from data_designer.config import DataDesignerConfigBuilder
    from data_designer.config.processors import ProcessorType

    recipe_core = {
        key: value
        for key, value in recipe.items()
        if key not in {"model_providers", "mcp_providers"}
    }
    recipe_core, oxc_local_callable_specs = split_oxc_local_callable_validators(
        recipe_core
    )
    builder = DataDesignerConfigBuilder.from_config({"data_designer": recipe_core})
    register_oxc_local_callable_validators(
        builder = builder,
        specs = oxc_local_callable_specs,
    )

    # DataDesignerConfigBuilder.from_config currently skips processors.
    # Re-attach explicitly so drop_columns/schema_transform survive API payload.
    for processor in recipe_core.get("processors") or []:
        if not isinstance(processor, dict):
            continue
        processor_type_raw = processor.get("processor_type")
        if not isinstance(processor_type_raw, str):
            continue
        kwargs = {k: v for k, v in processor.items() if k != "processor_type"}
        builder.add_processor(
            processor_type = ProcessorType(processor_type_raw),
            **kwargs,
        )

    return builder