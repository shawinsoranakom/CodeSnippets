def transform_data(
        query: FMPExecutiveCompensationQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[FMPExecutiveCompensationData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        import warnings

        symbols = query.symbol.split(",")
        filtered_results: list[FMPExecutiveCompensationData] = []

        for symbol in symbols:
            symbol_data = [item for item in data if item.get("symbol") == symbol]

            if symbol_data and query.year != 0:
                max_year_for_symbol = (
                    (
                        max(
                            item.get("year", 0)
                            for item in symbol_data
                            if item.get("year")
                        )
                    )
                    if query.year == -1
                    else query.year
                )
                symbol_max_year_data = [
                    item
                    for item in symbol_data
                    if int(item.get("year", 0)) == max_year_for_symbol
                ]
                if not symbol_max_year_data:
                    warnings.warn(
                        f"ValueError: No data found for {symbol} and year {query.year}."
                    )
                    continue

                filtered_results.extend(
                    [
                        FMPExecutiveCompensationData.model_validate(item)
                        for item in symbol_max_year_data
                    ]
                )
            else:
                filtered_results.extend(
                    [
                        FMPExecutiveCompensationData.model_validate(item)
                        for item in sorted(
                            symbol_data, key=lambda x: x.get("year", 0), reverse=True
                        )
                    ]
                )

        if not filtered_results:
            raise EmptyDataError("No data found for given symbols and year.")

        return filtered_results