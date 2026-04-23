def _register_module_fusion(
    cls: "type[PreTrainedModel]", config: "PretrainedConfig", fusion_name: str, spec: ModuleFusionSpec
) -> None:
    """Register one fusion family for `cls`.

    This function updates the two global registries used by fused loading:
    - the monkey-patching registry, so compatible module classes are replaced before initialization
    - the checkpoint conversion mapping, so fused runtime modules still load from the original checkpoint layout

    Notes:
    - conflicting checkpoint transforms fail fast
    """

    fusable_classes = _discover_fusable_modules(cls, config, fusion_name=fusion_name, spec=spec)
    if not fusable_classes:
        logger.info(spec.get_empty_log(cls.__name__))
        return

    register_patch_mapping(fusable_classes, overwrite=True)

    if not hasattr(cls, "config_class") or not hasattr(cls.config_class, "model_type"):
        raise ValueError(f"Model {cls.__name__} has no config class or model type")
    model_type = cls.config_class.model_type
    converters = spec.make_transforms(config)

    existing_converters = get_checkpoint_conversion_mapping(model_type)
    if existing_converters is not None:
        # WeightConverter matching stops at the first matching source pattern, so
        # conflicting converters must fail fast instead of being appended.
        existing_converter_sources = {tuple(existing.source_patterns): existing for existing in existing_converters}
        for converter in converters:
            source_patterns = tuple(converter.source_patterns)
            existing_converter = existing_converter_sources.get(source_patterns)
            if existing_converter is not None:
                raise ValueError(
                    f"Fusion {fusion_name} for model type {model_type} conflicts with an existing conversion mapping "
                    f"for source patterns {source_patterns}."
                )

        # TODO: allow compatible fusions mentioned https://github.com/huggingface/transformers/pull/45041#discussion_r3028989716
        converters = existing_converters + converters

    register_checkpoint_conversion_mapping(model_type, converters, overwrite=True)