def parse_context(  # pylint: disable=R0912, R0914, R0915
    response: list[dict], latest: bool = False, with_metadata: bool = False
) -> DataFrame | tuple[DataFrame, dict]:
    """Parse the output from `get_context()`, and optionally return the metadata."""
    metadata = {}
    results = DataFrame()
    if response is None:
        raise OpenBBError("No data was in the response")
    if not isinstance(response, list):
        raise OpenBBError("Expecting a list of dictionaries and received a dictionary.")
    for item in response:
        symbol = item.get("id", "")
        _symbol = symbol.split("~")[0].replace("19", "")
        temp_unit = ""
        temp_meta = item.get("td", {})
        temp_data = item.get("dataarray", [])
        temp_transform = symbol.split("~")[1] if "~" in symbol else ""
        temp_country = item.get("geography", {}).get("name", "")
        temp_country = temp_country.replace(" (19 countries)", "")
        # We need the metadata to process the results.
        if temp_meta:
            temp_unit = temp_meta.get("units", "")
            temp_scale = temp_meta.get("scale", "")
            if temp_transform:
                if temp_transform in ["TOYA", "TPOP", "TPGP"]:
                    temp_unit = "Percent"
                if temp_transform == "TUSD":
                    temp_unit = "USD"
                temp_transform = TRANSFORM_DICT.get(temp_transform, "")
            temp_multiplier = (
                1 if temp_unit == "Percent" else unit_multiplier(temp_scale.lower())
            )
            date_ranges = temp_meta.get("range", [])
            # We store the metadata for each indicator.
            metadata[_symbol] = dict(  # pylint: disable=R1735
                country=temp_country.title(),
                title=item.get("verbose_title", None),
                frequency=temp_meta.get("frequency", None),
                transformation=temp_transform if temp_transform else None,
                unit=temp_unit,
                unit_multiplier=temp_multiplier,
                scale=temp_unit if temp_unit == "Percent" else temp_scale,
                description=temp_meta.get("descrip_long", None),
                last_update=temp_meta.get("lastupdate", None),
                next_release=temp_meta.get("next_release", None),
                first_date=date_ranges[0] if date_ranges else None,
                last_date=date_ranges[1] if date_ranges else None,
                dataset=item.get("dataset", None),
            )
            if temp_data:
                temp_series = (
                    DataFrame(temp_data).set_index("date").sort_index().get(symbol)
                )
                temp_series.name = _symbol
                temp_series = temp_series.replace("nan", None).dropna()
                temp_series.name = temp_series.name[:-2]
                temp_series = temp_series.to_frame()
                temp_series["Country"] = metadata[_symbol].get("country")
                # To make the GDP data comparable across countries, it needs to be consistent.
                # We scale everything to billions for GDP. The data needs to be annualized for most countries.
                if "GDP" in symbol and temp_unit != "Percent":
                    temp_series[_symbol[:-2]] = (
                        temp_series[_symbol[:-2]].astype(float).dropna()
                    )
                    # For some countries, we need to annualize the GDP data.
                    if temp_country not in GDP_ADJUST:
                        temp_series[_symbol[:-2]] = (
                            temp_series[_symbol[:-2]].rolling(4).sum()
                        )
                    temp_series[_symbol[:-2]] = (
                        temp_series[_symbol[:-2]] * temp_multiplier
                    ) / 1000000000
                    # Update the metadata to reflect the new scale.
                    metadata[_symbol]["unit_multiplier"] = 1000000000
                    metadata[_symbol]["scale"] = "Billions"
                if "GDEBT" in symbol and temp_unit != "Percent":
                    # We apply the multiplier in the metadata to the data and then convert it to billions.
                    temp_series[_symbol[:-2]] = (
                        temp_series[_symbol[:-2]].astype(float) * temp_multiplier
                    ) / 1000000000
                if "POP" in symbol and temp_unit != "Percent":
                    temp_series[_symbol[:-2]] = (
                        temp_series[_symbol[:-2]].astype(int).dropna()
                    )
                    # We don't use the metadata multiplier here because it is not always accurate.
                    if temp_country in POP_MULTIPLIER:
                        temp_series[_symbol[:-2]] = (
                            temp_series[_symbol[:-2]] * POP_MULTIPLIER[temp_country]
                        )
                        metadata[_symbol]["unit_multiplier"] = POP_MULTIPLIER[
                            temp_country
                        ]
                # If we are just getting the latest data, clip it.
                if latest is True:
                    temp_series = temp_series.set_index("Country").tail(1)
                results = concat([results, temp_series], axis=0)
    if with_metadata is True:
        return results, metadata
    return results