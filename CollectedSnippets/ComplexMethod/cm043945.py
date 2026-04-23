def _build_dimension_lookups(
    dataflow: str, metadata
) -> tuple[dict[str, str], dict[str, set[str]], list[str]]:
    """
    Build lookups for mapping codes to dimensions.

    Returns (code_to_dimension, codes_by_dimension, dimension_order) tuple.
    - code_to_dimension: maps any valid code to its dimension ID (for parsing)
    - codes_by_dimension: maps dimension ID to valid individual codes (for validation messages)
    - dimension_order: list of dimension IDs in their proper order from DSD
    """
    # pylint: disable=import-outside-toplevel
    from collections import defaultdict

    code_to_dimension: dict[str, str] = {}
    codes_by_dimension: dict[str, set[str]] = defaultdict(set)
    dimension_order: list[str] = []

    # Get ALL dimension codes from parameters API (authoritative source)
    # This provides the actual valid values for each dimension
    try:
        all_params = metadata.get_dataflow_parameters(dataflow)
        # Exclude time-related dimensions and country/area dimensions from indicator lookup
        # Country is handled separately via the 'country' parameter
        exclude_dims = {"FREQUENCY", "TIME_PERIOD", "COUNTRY", "REF_AREA"}
        for dim_id, values in all_params.items():
            if dim_id in exclude_dims:
                continue
            for v in values:
                code = v.get("value")
                if code:
                    # Add to codes_by_dimension (authoritative source for validation)
                    codes_by_dimension[dim_id].add(code)
                    # Add to code_to_dimension for matching
                    if code not in code_to_dimension:
                        code_to_dimension[code] = dim_id
    except Exception:  # noqa
        pass  # Continue with indicator-only lookup if params unavailable

    # Get dimension order from DSD
    # Keep COUNTRY/REF_AREA in order (they define the first segment position)
    # Exclude trailing dimensions that are always separate parameters
    try:
        df_obj = metadata.dataflows.get(dataflow, {})
        dsd_id = df_obj.get("structureRef", {}).get("id")
        if dsd_id and dsd_id in metadata.datastructures:
            dsd = metadata.datastructures[dsd_id]
            # Only exclude trailing parameter dimensions
            trailing_dims = {
                "FREQUENCY",
                "TIME_PERIOD",
                "TYPE_OF_TRANSFORMATION",
                "TRANSFORMATION",
            }
            for dim in dsd.get("dimensions", []):
                dim_id = dim.get("id", "")
                if (
                    dim_id
                    and dim_id.upper() not in trailing_dims
                    and "TRANSFORM" not in dim_id.upper()
                ):
                    dimension_order.append(dim_id)
    except Exception:  # noqa
        pass

    return code_to_dimension, dict(codes_by_dimension), dimension_order