def get_model_conversion_mapping(
    model: PreTrainedModel,
    key_mapping: dict[str, str] | None = None,
    hf_quantizer: HfQuantizer | None = None,
    add_legacy: bool = True,
) -> list[WeightTransform]:
    """
    For a given `model`, obtain the weight conversion mapping if any are registered either as a simple renaming
    `_checkpoint_conversion_mapping` class argument, or in the general WeightConverter mapping.
    """
    # Lazy import to avoid circular import issues
    from .modeling_utils import PreTrainedModel

    # note: this function is used in PEFT, so changing the API requires coordination
    weight_conversions = []

    # Load models with explicit, user-provided key mapping
    if key_mapping is not None:
        weight_conversions = [WeightRenaming(source_patterns=k, target_patterns=v) for k, v in key_mapping.items()]

    # Model have several `PreTrainedModel` within with the same model type, for example: XForConditionalGeneration -> XModel
    # We don't want to apply the same conversion pattern twice because of that
    seen_model_types = set()
    # Recurse over submodules and collect all conversions
    for name, submodule in model.named_modules():
        if isinstance(submodule, PreTrainedModel) and submodule.config.model_type not in seen_model_types:
            conversions = extract_weight_conversions_for_model(submodule, name)
            if conversions is not None:
                weight_conversions.extend(conversions)
                seen_model_types.add(submodule.config.model_type)

    if add_legacy:
        weight_conversions.extend(get_checkpoint_conversion_mapping("legacy"))

    # Add the ones from the quantizer as well if provided
    if hf_quantizer is not None:
        weight_conversions.extend(hf_quantizer.get_weight_conversions())

    return weight_conversions