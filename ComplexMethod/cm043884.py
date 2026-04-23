async def presentation_table_choices(
    dataflow_group: str | None = None,
    table: str | None = None,
    country: str | None = None,
    frequency: str | None = None,
) -> list[dict[str, str]]:
    """Get presentation table choices for IMF data retrieval.

    This endpoint provides dynamic choices for IMF presentation tables based on selected parameters.
    It is intended to be used by the OpenBB Workspace UI to populate dropdowns.

    For manual API calls, use `economy/indicators` instead with a `symbol` from `list_tables()`.

    Parameters
    ----------
    dataflow_group : str | None
        The IMF dataflow group. Show all groups if None.
    table : str | None
        The IMF presentation table ID. Enter a dataflow_group to see table choices.
    country : str | None
        Enter a dataflow_group and table to see country choices.
    frequency : str | None
        Enter a dataflow_group, table, and country to see frequency choices.

    Returns
    -------
    list[dict[str, str]]
        A list of dictionaries with 'label' and 'value' for each presentation table.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_imf.utils.progressive_helper import ImfParamsBuilder

    choices: list[dict[str, str]] = []

    if dataflow_group is None:
        return table_dataflow_choices

    metadata = ImfMetadata()

    if dataflow_group is not None and table is None:

        table_names = table_dataflow_map.get(dataflow_group, [])

        for t in table_names:
            choices.append(
                {
                    "label": table_name_map.get(t, t),
                    "value": t,
                }
            )

        return choices

    if dataflow_group is not None and table is not None and country is None:
        table_id = PRESENTATION_TABLES.get(table, "")
        dataflow_id = table_id.split("::")[0]
        params = metadata.get_dataflow_parameters(dataflow_id)
        country_dim = (
            "COUNTRY"
            if "COUNTRY" in params
            else "JURISDICTION" if "JURISDICTION" in params else "REF_AREA"
        )
        countries = params.get(country_dim, [])

        return sorted(countries, key=lambda x: x["label"])

    if dataflow_group is not None and table is not None and country is not None:
        table_id = PRESENTATION_TABLES.get(table, "")
        dataflow_id = table_id.split("::")[0]
        hierarchy_id = table_id.split("::", 1)[1] if "::" in table_id else None
        params = metadata.get_dataflow_parameters(dataflow_id)
        country_dim = "COUNTRY" if "COUNTRY" in params else "REF_AREA"
        freq_dim = "FREQUENCY" if "FREQUENCY" in params else "FREQ"

        # Get table structure and extract dimension codes (same as table_builder.get_table)
        table_structure = metadata.get_dataflow_table_structure(
            dataflow_id, hierarchy_id
        )
        dimension_codes: dict[str, list[str]] = {}
        for entry in table_structure.get("indicators", []):
            indicator_code = entry.get("indicator_code")
            dimension_id = entry.get("dimension_id")
            if indicator_code and dimension_id:
                if dimension_id not in dimension_codes:
                    dimension_codes[dimension_id] = []
                if indicator_code not in dimension_codes[dimension_id]:
                    dimension_codes[dimension_id].append(indicator_code)

        pb = ImfParamsBuilder(dataflow_id=dataflow_id)
        dims_in_order = pb._get_dimensions_in_order()

        # Set dimensions in order, using table's indicator codes
        for dim_id in dims_in_order:
            if dim_id in dimension_codes:
                codes = dimension_codes[dim_id]
                joined = "+".join(codes)
                if len(joined) > 800:
                    # Truncate to avoid URL length issues
                    joined = "+".join(codes[:20])
                    if len(joined) > 800:
                        joined = "*"
                pb.set_dimension((dim_id, joined))
            elif dim_id == country_dim:
                pb.set_dimension((dim_id, str(country).replace(",", "+")))

        options = pb.get_options_for_dimension(freq_dim) if freq_dim else []

        return options

    if (
        dataflow_group is not None
        and table is not None
        and country is not None
        and frequency is not None
    ):
        table_id = PRESENTATION_TABLES.get(table, "")
        dataflow_id = table_id.split("::")[0]
        hierarchy_id = table_id.split("::", 1)[1] if "::" in table_id else None
        params = metadata.get_dataflow_parameters(dataflow_id)
        country_dim = "COUNTRY" if "COUNTRY" in params else "REF_AREA"
        freq_dim = "FREQUENCY" if "FREQUENCY" in params else "FREQ"

        # Get table structure and extract dimension codes (same as table_builder.get_table)
        table_structure = metadata.get_dataflow_table_structure(
            dataflow_id, hierarchy_id
        )
        dimension_codes = {}
        for entry in table_structure.get("indicators", []):
            indicator_code = entry.get("indicator_code")
            dimension_id = entry.get("dimension_id")
            if indicator_code and dimension_id:
                if dimension_id not in dimension_codes:
                    dimension_codes[dimension_id] = []
                if indicator_code not in dimension_codes[dimension_id]:
                    dimension_codes[dimension_id].append(indicator_code)

        pb = ImfParamsBuilder(dataflow_id=dataflow_id)
        dims_in_order = pb._get_dimensions_in_order()

        # Set dimensions in order, using table's indicator codes
        for dim_id in dims_in_order:
            if dim_id in dimension_codes:
                codes = dimension_codes[dim_id]
                joined = "+".join(codes)
                if len(joined) > 800:
                    joined = "+".join(codes[:20])
                    if len(joined) > 800:
                        joined = "*"
                pb.set_dimension((dim_id, joined))
            elif dim_id == country_dim:
                pb.set_dimension((dim_id, str(country).replace(",", "+")))
            elif dim_id == freq_dim:
                pb.set_dimension((dim_id, frequency))

        transform_dim = (
            "TYPE_OF_TRANSFORMATION" if "TYPE_OF_TRANSFORMATION" in params else None
        )
        options = pb.get_options_for_dimension(transform_dim) if transform_dim else []

        return options

    return choices