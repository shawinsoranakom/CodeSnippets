async def indicator_choices(  # noqa: PLR0912
    symbol: str | None = None,
    country: str | None = None,
    frequency: str | None = None,
    transform: str | None = None,
    dimension_values: list[str] | None = None,
) -> list[dict[str, str]]:
    """Get progressive indicator choices for IMF data retrieval.

    This endpoint works progressively starting with the 'symbol' parameter,
    which is required and in the format 'dataflow::indicator'.

    Function is not intended to be used directly;
    it is used by the OpenBB Workspace for progressive parameter selection.

    For manual inspection, use the `get_dataflow_dimensions` endpoint instead.

    Parameters
    ----------
    symbol : str | None
        The IMF dataflow and indicator code in the format 'dataflow::indicator'.
        No symbol will return an empty list. Use `economy/available_indicators` to see available symbols.
    country : str | None
        Enter a symbol and leave country as None to see country choices.
    frequency : str | None
        Enter a symbol and country to see frequency choices.
    transform : str | None
        Enter a symbol, country, and frequency to see transform choices.
    dimension_values : list[str] | None
        Additional dimension filters in 'DIM_ID:VALUE' format to constrain choices.

    Returns
    -------
    list[dict[str, str]]
        A list of dictionaries with 'label' and 'value' for each choice.
    """
    # pylint: disable=import-outside-toplevel
    from urllib.parse import unquote

    from openbb_imf.utils.helpers import detect_transform_dimension

    metadata = ImfMetadata()

    # Symbol is required and in format dataflow::indicator
    if symbol is None:
        return []

    # URL-decode the symbol parameter and handle multiple comma-separated symbols
    symbol = unquote(symbol)

    # Parse multiple symbols (comma-separated): "QGFS::F4_L_T_XDC,QGFS::F12_L_T_XDC"
    symbols = [s.strip() for s in symbol.split(",") if s.strip()]
    if not symbols:
        return []

    # Extract unique dataflows and all indicator codes
    dataflows_seen: set[str] = set()
    indicator_codes: list[str] = []

    for sym in symbols:
        if "::" in sym:
            df_id = sym.split("::")[0].strip()
            ind_code = sym.split("::", 1)[1].strip()
            dataflows_seen.add(df_id)
            if ind_code:
                indicator_codes.append(ind_code)
        else:
            # Just a dataflow ID with no indicator
            dataflows_seen.add(sym.strip())

    # For now, only support single dataflow (use first one)
    dataflow_id = list(dataflows_seen)[0] if dataflows_seen else None
    indicator_code = "+".join(indicator_codes) if indicator_codes else None

    if not dataflow_id:
        return []

    # Get dimension order for this dataflow
    df_obj = metadata.dataflows.get(dataflow_id, {})

    if not df_obj:
        return []

    dsd_id = df_obj.get("structureRef", {}).get("id")
    dsd = metadata.datastructures.get(dsd_id, {})
    dimensions = dsd.get("dimensions", [])

    # Sort by position
    sorted_dims = sorted(
        [d for d in dimensions if d.get("id") != "TIME_PERIOD"],
        key=lambda x: int(x.get("position", 0)),
    )
    dim_order = [d["id"] for d in sorted_dims]

    # Get codelist labels for all dimensions
    params = metadata.get_dataflow_parameters(dataflow_id)

    # Identify dimension types
    country_dim = "COUNTRY" if "COUNTRY" in dim_order else "REF_AREA"
    freq_dim = "FREQUENCY" if "FREQUENCY" in dim_order else "FREQ"
    transform_dim, unit_dim, _, _ = detect_transform_dimension(dataflow_id)
    # Use UNIT dimension as fallback for transform if no transform dimension exists
    effective_transform_dim = transform_dim or unit_dim

    # Parse dimension_values into a dict of DIM_ID -> VALUE
    # Input format: list of "DIM_ID:VALUE" strings
    extra_dimensions: dict[str, str] = {}
    if dimension_values:
        for dv in dimension_values:
            if not dv or not isinstance(dv, str):
                continue
            if ":" in dv:
                dim_id, dim_value = dv.split(":", 1)
                extra_dimensions[dim_id.strip().upper()] = dim_value.strip().upper()

    # dimension_values OVERRIDES parameter values for country/frequency/transform
    # Check if any country dimension is in extra_dimensions
    for cdim in ("COUNTRY", "REF_AREA", "JURISDICTION", "AREA"):
        if cdim in extra_dimensions:
            country = extra_dimensions.pop(cdim)
            break
    # Check if frequency dimension is in extra_dimensions
    for fdim in ("FREQUENCY", "FREQ"):
        if fdim in extra_dimensions:
            frequency = extra_dimensions.pop(fdim)
            break
    # Check if transform dimension is in extra_dimensions
    for tdim in ("UNIT_MEASURE", "UNIT", "TRANSFORMATION"):
        if tdim in extra_dimensions:
            transform = extra_dimensions.pop(tdim)
            break

    # Find indicator dimension - check which dimension contains the indicator_code
    # This list should include all possible indicator-type dimensions across dataflows
    indicator_dims = [
        "INDICATOR",
        "INDEX_TYPE",
        "COICOP_1999",
        "SERIES",
        "ITEM",
        "BOP_ACCOUNTING_ENTRY",
        "ACCOUNTING_ENTRY",
        "PRODUCTION_INDEX",
    ]

    # If we have indicator_code(s), find which dimension they belong to
    # indicator_code may be "+" joined (e.g., "F4_L_T_XDC+F12_L_T_XDC")
    indicator_dim = None
    first_indicator = indicator_code.split("+")[0] if indicator_code else None
    if first_indicator:
        for dim_id in indicator_dims:
            if dim_id in dim_order:
                dim_values = {p.get("value") for p in params.get(dim_id, [])}
                if first_indicator in dim_values:
                    indicator_dim = dim_id
                    break

        # If still not found, search ALL dimensions for the indicator code
        if indicator_dim is None:
            for dim_id in dim_order:
                if dim_id in (
                    country_dim,
                    freq_dim,
                    transform_dim,
                    unit_dim,
                    "TIME_PERIOD",
                ):
                    continue  # Skip known non-indicator dimensions
                dim_values = {p.get("value") for p in params.get(dim_id, [])}
                if first_indicator in dim_values:
                    indicator_dim = dim_id
                    break

    # Fallback to first available indicator dimension if not found
    if indicator_dim is None:
        indicator_dim = next((d for d in indicator_dims if d in dim_order), None)

    def build_key_with_indicator(target_dim: str) -> str:
        """Build constraint key with indicator always set, targeting a specific dimension.

        This builds a full key for all dimensions, with the target dimension as wildcard
        and the indicator dimension set to the indicator code (if available).
        This allows querying for available values of the target dimension filtered by indicator.
        """
        key_parts: list[str] = []
        for dim_id in dim_order:
            if dim_id == target_dim:
                # Target dimension gets wildcard - we want to know available values
                key_parts.append("*")
            elif dim_id == country_dim:
                key_parts.append(str(country).replace(",", "+") if country else "*")
            elif dim_id == indicator_dim:
                # Always include indicator code if available
                key_parts.append(indicator_code if indicator_code else "*")
            elif dim_id == freq_dim:
                key_parts.append(str(frequency) if frequency else "*")
            elif dim_id in (transform_dim, unit_dim):
                key_parts.append(
                    str(transform) if transform and transform != "true" else "*"
                )
            elif dim_id in extra_dimensions:
                # Use value from dimension_values if provided
                key_parts.append(extra_dimensions[dim_id])
            else:
                key_parts.append("*")

        return ".".join(key_parts)

    def get_choices_for_dim(dim_id: str) -> list:
        """Get available choices for a dimension using constraints API."""
        key = build_key_with_indicator(dim_id)
        constraints = metadata.get_available_constraints(
            dataflow_id=dataflow_id,
            key=key,
            component_id=dim_id,
        )
        # Get labels from params
        labels = {opt["value"]: opt["label"] for opt in params.get(dim_id, [])}
        # Also try to get labels from codelist
        codelist_labels: dict = {}
        dim_meta: dict = next((d for d in sorted_dims if d.get("id") == dim_id), {})

        if dim_meta:
            codelist_id = metadata._resolve_codelist_id(
                dataflow_id, dsd_id, dim_id, dim_meta
            )

            if codelist_id and codelist_id in metadata._codelist_cache:
                codelist_labels = metadata._codelist_cache.get(codelist_id, {})

        choices: list = []

        for kv in constraints.get("key_values", []):
            if kv.get("id") == dim_id:
                for value in kv.get("values", []):
                    # Try params first, then codelist, then fall back to value
                    label = labels.get(value) or codelist_labels.get(value) or value
                    choices.append({"label": label, "value": value})

        return choices

    # Step 1: No country selected - return country choices filtered by indicator
    if country == "true" and country_dim:
        choices = get_choices_for_dim(country_dim)
        choices = sorted(choices, key=lambda x: x["label"])
        choices.insert(0, {"label": "All Countries", "value": "*"})
        return choices

    # Step 2: Country selected, no frequency - return frequency choices
    if frequency == "true" and freq_dim:
        return get_choices_for_dim(freq_dim)

    # Step 3: Frequency selected, no transform - return transform choices
    if transform == "true" and effective_transform_dim:
        choices = get_choices_for_dim(effective_transform_dim)
        # Add "all" option at the beginning if there are choices
        if choices:
            choices.insert(0, {"label": "All", "value": "all"})
        return choices

    # All parameters set - no more choices needed
    return []