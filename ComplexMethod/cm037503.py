def recursively_merge_kwargs(
    defaults: dict[str, Any] | None,
    overrides: dict[str, Any] | None,
    /,
    *,
    unset_values: tuple[object, ...] = (None, "auto"),
) -> dict[str, Any]:
    if defaults is None:
        defaults = {}
    if overrides is None:
        overrides = {}

    merged = dict(defaults)

    for k, v in overrides.items():
        if v in unset_values:
            continue

        if k in merged and isinstance(merged[k], dict) and isinstance(v, dict):
            merged[k] = recursively_merge_kwargs(
                merged[k], v, unset_values=unset_values
            )
        else:
            merged[k] = v

    return merged