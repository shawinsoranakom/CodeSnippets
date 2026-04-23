def imts_query(
    country: str | list[str],
    counterpart: str | list[str],
    indicator: str | list[str],
    freq: str = "A",
    start_date: str | None = None,
    end_date: str | None = None,
    **kwargs,
) -> dict:
    """Query the Direction of Trade (IMTS) dataset.
    This function handles input validation for countries and counterparts.

    Parameters
    ----------
    country : str | list[str]
        The country or countries to fetch data for.
    counterpart : str | list[str]
        The counterpart country or countries. Use "*" for all.
    indicator : str | list[str]
        The indicator or indicators to fetch. Use "*" for all.
    freq : str | None
        The frequency of the data, by default "A" (annual).
    start_date : str | None
        The start date of the data, by default None.
    end_date : str | None
        The end date of the data, by default None.
    **kwargs : dict
        Additional query parameters to pass to the API.

    Returns
    -------
    dict
        A dictionary with keys: 'data' containing the fetched data,
        and 'metadata' containing the related metadata.
    """
    # pylint: disable=import-outside-toplevel
    from openbb_imf.utils.query_builder import ImfQueryBuilder

    if not country or not counterpart:
        raise ValueError("Country and counterpart parameters cannot be empty.")

    freq = freq[0].upper()

    if freq and freq not in ["A", "Q", "M"]:
        raise ValueError("Frequency must be one of 'A', 'Q', or 'M'.")

    query_builder = ImfQueryBuilder()
    dataflow_id = "IMTS"
    params = query_builder.metadata.get_dataflow_parameters(dataflow_id)
    country_values = {item["value"] for item in params.get("COUNTRY", [])}
    counterpart_values = {
        item["value"]
        for item in params.get("COUNTERPART_COUNTRY", params.get("COUNTRY", []))
    }

    def _validate_selection(selection, valid_values, name):
        """Validate country or counterpart selection."""
        if not valid_values:
            return selection

        # Handle wildcards - return "*" as-is
        if selection == "*":
            return "*"

        # Parse the selection into a list
        if isinstance(selection, str):
            # Check if it contains commas (comma-separated list)
            selection_list = (
                [item.strip() for item in selection.split(",")]
                if "," in selection
                else [selection]
            )
        else:
            selection_list = selection

        # Check if any item is a wildcard
        if "*" in selection_list:
            return "*"

        invalid = [item for item in selection_list if item not in valid_values]
        if invalid:
            raise ValueError(f"Invalid {name}(s): {', '.join(invalid)}")
        return selection_list if len(selection_list) > 1 else selection_list[0]

    validated_country = _validate_selection(country, country_values, "country")
    validated_counterpart = _validate_selection(
        counterpart, counterpart_values, "counterpart"
    )

    # For indicator, handle wildcards and comma-separated values the same way
    if isinstance(indicator, str) and "," in indicator:
        validated_indicator = [item.strip() for item in indicator.split(",")]
    else:
        validated_indicator = indicator if indicator != "*" else "*"  # type: ignore

    return query_builder.fetch_data(
        dataflow=dataflow_id,
        start_date=start_date,
        end_date=end_date,
        FREQUENCY=freq,
        COUNTRY=validated_country,
        COUNTERPART_COUNTRY=validated_counterpart,
        INDICATOR=validated_indicator,
        **kwargs,
    )