def detect_transform_dimension(
    dataflow: str,
) -> tuple[str | None, str | None, dict[str, str], dict[str, str]]:
    """
    Detect transformation and unit dimensions for a dataflow.

    Dynamically finds dimensions containing 'TRANSFORM' or 'UNIT' in their names.

    Returns:
        tuple of (transform_dim, unit_dim, transform_lookup, unit_lookup) where:
        - transform_dim: name of transform dimension (or None)
        - unit_dim: name of unit dimension (or None)
        - transform_lookup: maps user-friendly names (index, yoy, period) to IMF codes
        - unit_lookup: maps user-friendly names (usd, eur, index, local) to IMF codes
    """
    # pylint: disable=import-outside-toplevel
    from openbb_imf.utils.metadata import ImfMetadata

    transform_dim: str | None = None
    unit_dim: str | None = None
    transform_lookup: dict[str, str] = {}
    unit_lookup: dict[str, str] = {}

    try:
        m = ImfMetadata()
        params = m.get_dataflow_parameters(dataflow)

        for dim, values in params.items():
            dim_upper = dim.upper()

            # Handle TRANSFORM dimension
            if "TRANSFORM" in dim_upper:
                transform_dim = dim
                for v in values:
                    code = v.get("value", "")
                    label = v.get("label", "").lower()

                    # Prefer simpler codes (shorter, no prefix like SRP_, WGT, SA_)
                    is_simple = (
                        not code.startswith("SRP_")
                        and not code.startswith("WGT")
                        and not code.startswith("SA_")
                    )

                    # Index: just "Index" without change/percent
                    if (
                        label == "index"
                        or (
                            "index" in label
                            and "change" not in label
                            and "percent" not in label
                        )
                    ) and ("index" not in transform_lookup or is_simple):
                        transform_lookup["index"] = code

                    # YOY: year-over-year or year ago
                    if (
                        "year-over-year" in label
                        or "yoy" in label
                        or "year ago" in label
                    ) and ("yoy" not in transform_lookup or is_simple):
                        transform_lookup["yoy"] = code

                    # Period: period-over-period (not year-over-year)
                    if (
                        "period-over-period" in label
                        or (
                            "period" in label
                            and "change" in label
                            and "year" not in label
                        )
                    ) and ("period" not in transform_lookup or is_simple):
                        transform_lookup["period"] = code

                    if ("percent of gdp" in label or "% of gdp" in label) and (
                        "percent_gdp" not in transform_lookup or is_simple
                    ):
                        transform_lookup["percent_gdp"] = code

                    # Currency / Domestic currency (for GFS dataflows)
                    if ("domestic currency" in label or label == "currency") and (
                        "currency" not in transform_lookup or is_simple
                    ):
                        transform_lookup["currency"] = code

                    # Also allow direct code access (case-insensitive)
                    transform_lookup[code.lower()] = code

            # Handle UNIT dimension
            elif dim_upper == "UNIT":
                unit_dim = dim
                for v in values:
                    code = v.get("value", "")
                    label = v.get("label", "").lower()

                    # Map common unit names
                    if "us dollar" in label or label == "usd":
                        unit_lookup["usd"] = code
                    if "euro" in label or label == "eur":
                        unit_lookup["eur"] = code
                    if label == "index" or "index" in label:
                        unit_lookup["index"] = code
                    if "local" in label or "national" in label or "domestic" in label:
                        unit_lookup["local"] = code
                    if "percent" in label or "%" in label:
                        unit_lookup["percent"] = code

                    # Also allow direct code access (case-insensitive)
                    unit_lookup[code.lower()] = code

    except (KeyError, ValueError):
        pass

    return transform_dim, unit_dim, transform_lookup, unit_lookup