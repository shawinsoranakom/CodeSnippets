def transform_data(  # pylint: disable=R0914,R0915
        query: EconDbEconomicIndicatorsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> AnnotatedResult[list[EconDbEconomicIndicatorsData]]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils import helpers
        from pandas import DataFrame, concat

        if query.symbol.upper() == "MAIN":
            return AnnotatedResult(
                result=[
                    EconDbEconomicIndicatorsData.model_validate(r)
                    for r in data[0].get("records", [])
                ],
                metadata={query.country: data[0].get("metadata", [])},
            )
        output = DataFrame()
        metadata = {}
        for d in data:
            if "data" in d and not d["data"].get("values"):
                warn(
                    f"Symbol Error: No data found for '{d.get('ticker', '')}'."
                    + " The country has data, but not for the requested date range."
                )
                continue
            # First we need to parse the metadata for the series.
            title = d.get("description", "")
            title = title.replace("All countries", "World")
            _symbol = d.get("ticker", [])
            symbol = _symbol.split("~")[0] if "~" in _symbol else _symbol
            indicator = helpers.SYMBOL_TO_INDICATOR.get(symbol, "")
            _transform = _symbol.split("~")[1] if "~" in _symbol else ""
            transform = helpers.TRANSFORM_DICT.get(_transform, None)
            country = d.get("geography", "")
            country = country.replace("All countries", "World")
            frequency = d.get("frequency", None)
            dataset = d.get("dataset", None)
            units = helpers.UNITS.get(symbol, "")
            scale = (
                "PERCENT"
                if _transform in ["TPGP", "TPOP", "TOYA"]
                else helpers.SCALES.get(symbol, None)
            )
            if symbol.startswith("Y10YD") or symbol.startswith("M3YD"):
                scale = "Units"
                units = "PERCENT"
            add_info = d.get("additional_metadata", None) or d.get(
                "additional_info", None
            )
            if _transform == "TUSD":
                scale = "Units"
                units = "USD"
            if add_info:
                if (
                    scale in ["Units", "PERCENT"]
                    and units == "DOMESTIC"
                    and "COMMODITY:Commodity" in add_info
                ):
                    units = "USD"
                elif scale == "Units":
                    units = (
                        add_info.get(
                            "UNIT_MEASURE:UNIT_MEASURE",
                            add_info.get("UNIT:Unit of measure", units),
                        )
                        if units != "USD"
                        else units
                    )
            units = units.replace("PC:Percentage", "PERCENT")
            if ", " in units:
                units = units.split(", ")[1]
            multiplier = 1 if scale == "PERCENT" else helpers.MULTIPLIERS.get(symbol, 1)
            # Special handling for the population multiplier
            # because some values are buried elsewhere in the metadata.
            if indicator == "POP" and country in helpers.POP_MULTIPLIER:
                multiplier = helpers.POP_MULTIPLIER[country]
            metadata.update(
                {
                    _symbol: dict(  # pylint: disable=R1735
                        title=title,
                        country=country,
                        frequency=frequency,
                        dataset=dataset,
                        transform=transform if transform else None,
                        units=units if units else None,
                        scale=scale if scale else None,
                        multiplier=multiplier if multiplier else None,
                        additional_info=add_info if add_info else None,
                    )
                }
            )
            # Now we can get the data.
            _result = d.get("data", [])
            result = DataFrame(_result)
            result = result.rename(
                columns={"dates": "date", "values": "value"}
            )[  # pylint: disable=E1136  # type: ignore
                ["date", "value"]
            ].sort_values(
                by="date"
            )
            result["symbol_root"] = indicator
            result["symbol"] = _symbol
            result["country"] = country
            # We can normalize the percent values here
            # because we have accounted for transformation, if done.
            if units == "PERCENT" or scale == "PERCENT":
                result["value"] = result["value"].astype(float).div(100)
            # Combine it with all the other series requested.
            output = concat([output, result.dropna()], axis=0)
            output = (
                output.set_index(["date", "symbol_root", "country"])
                .sort_index()
                .reset_index()
            )
        if output.empty:
            raise EmptyDataError(
                "Error: The no data was found for the supplied symbols and countries: "
                + f"{query.symbol.split(',')} {query.country.split(',') if query.country else ''}"
            )
        records = (
            output.fillna("N/A")
            .replace("N/A", None)
            .replace("nan", None)
            .replace("", None)
            .replace(0, None)
            .to_dict("records")
        )
        return AnnotatedResult(
            result=[
                EconDbEconomicIndicatorsData.model_validate(r)
                for r in records
                if r["value"] is not None
            ],
            metadata=metadata,
        )