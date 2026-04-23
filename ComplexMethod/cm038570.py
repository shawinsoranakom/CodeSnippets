def _merge_embeds(
    data_items: list[dict[str, "torch.Tensor"]],
    mm_processor: BaseMultiModalProcessor,
):
    if not data_items:
        return {}

    first_keys = set(data_items[0].keys())
    if any(set(item.keys()) != first_keys for item in data_items[1:]):
        raise ValueError(
            "All dictionaries in the list of embeddings must have the same keys."
        )

    fields = {
        key: _detect_field([item[key] for item in data_items], mm_processor)
        for key in first_keys
    }
    data_merged = {
        key: field._reduce_data([item[key] for item in data_items], pin_memory=False)
        for key, field in fields.items()
    }

    try:
        # TODO: Support per-request mm_processor_kwargs
        parsed_configs = mm_processor._get_mm_fields_config(
            transformers.BatchFeature(data_merged),
            {},
        )
        parsed_fields = {key: parsed_configs[key].field for key in first_keys}
        keys_to_update = [
            key
            for key in first_keys
            if (
                fields[key] != parsed_fields[key]
                and not isinstance(fields[key], _BatchedSingleItemField)
            )
        ]

        for key in keys_to_update:
            data_merged[key] = parsed_fields[key]._reduce_data(
                [item[key] for item in data_items], pin_memory=False
            )
    except Exception:
        logger.exception(
            "Error when parsing merged embeddings. "
            "Falling back to auto-detected fields."
        )

    return data_merged