def transform_data(
        query: TmxEquityQuoteQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[TmxEquityQuoteData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        from numpy import nan

        # Remove the items associated with `equity.profile()`.
        items_list = [
            "shortDescription",
            "longDescription",
            "website",
            "phoneNumber",
            "fullAddress",
            "email",
            "issueType",
            "exchangeName",
            "employees",
            "exShortName",
        ]
        data = [{k: v for k, v in d.items() if k not in items_list} for d in data]
        # Replace all NaN values with None.
        for d in data:
            for k, v in d.items():
                if v in (nan, 0, ""):
                    d[k] = None
        # Sort the data by the order of the symbols in the query.
        symbols = query.symbol.split(",")
        symbol_to_index = {symbol: index for index, symbol in enumerate(symbols)}
        data = sorted(data, key=lambda d: symbol_to_index[d["symbol"]])

        return [TmxEquityQuoteData.model_validate(d) for d in data]