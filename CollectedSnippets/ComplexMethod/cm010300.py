def _fx_collection_equivalence_fn(
    spec1_type: type | None,
    spec1_context: pytree.Context,
    spec2_type: type | None,
    spec2_context: pytree.Context,
) -> bool:
    """Treat containers and their immutable variants as the same type. Otherwise
    compare as normal.
    """
    if spec1_type is None or spec2_type is None:
        return spec1_type is spec2_type and spec1_context == spec2_context

    if issubclass(spec1_type, (dict, immutable_dict)) and issubclass(
        spec2_type, (dict, immutable_dict)
    ):
        return spec1_context == spec2_context

    if issubclass(spec1_type, (list, immutable_list)) and issubclass(
        spec2_type, (list, immutable_list)
    ):
        return spec1_context == spec2_context

    return spec1_type is spec2_type and spec1_context == spec2_context