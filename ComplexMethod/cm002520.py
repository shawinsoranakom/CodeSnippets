def rename_source_key(
    source_key: str,
    weight_renamings: list[WeightRenaming],
    weight_converters: list[WeightConverter],
    prefix: str | None = None,
    meta_state_dict: dict | None = None,
) -> tuple[str, str | None]:
    """
    Rename a source key given all the renaming and weight conversion patterns we have. Also takes care of adding/removing
    the base model prefix during loading if necessary.
    """
    renamed_key = source_key
    # 1. apply all renamings in turns (if multiple match, it's the responsibility of the mappings to make sure they
    # are coherent)
    for renaming in weight_renamings:
        renamed_key, _ = renaming.rename_source_key(renamed_key)

    # 2. apply renaming through weight conversions on the key if we have any WeightConverter (here we stop after
    # the first match, as we assume only 1 converter can match any source key)
    source_pattern = None
    for converter in weight_converters:
        renamed_key, source_pattern = converter.rename_source_key(renamed_key)
        if source_pattern is not None:
            break

    # 3. check if we need to add or remove prefix if necessary (only during loading, not saving)
    if prefix is not None and meta_state_dict is not None:
        if (
            renamed_key.startswith(prefix)
            and meta_state_dict.get(re.sub(f"^{prefix}.", "", renamed_key, count=1)) is not None
        ):
            renamed_key = re.sub(f"^{prefix}.", "", renamed_key, count=1)
        elif meta_state_dict.get(f"{prefix}.{renamed_key}") is not None:
            renamed_key = f"{prefix}.{renamed_key}"

    return renamed_key, source_pattern