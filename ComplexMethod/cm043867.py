def transform_data(
        query: EiaShortTermEnergyOutlookQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[EiaShortTermEnergyOutlookData]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from pandas import Categorical, DataFrame, to_datetime

        symbols = (
            query.symbol.upper().split(",")
            if query.symbol
            else [d.upper() for d in SteoTableMap[query.table]]
        )
        seen = set()
        unique_symbols: list = []
        for symbol in symbols:
            if symbol not in seen:
                unique_symbols.append(symbol)
                seen.add(symbol)
        symbols = unique_symbols

        table = query.table
        df = DataFrame(data)
        df.period = to_datetime(df.period).dt.date
        df.seriesId = Categorical(df.seriesId, categories=symbols, ordered=True)
        df = df.sort_values(["period", "seriesId"])
        df = df.reset_index(drop=True)
        returned_symbols = df.seriesId.unique().tolist()
        missing_symbols = [s for s in symbols if s not in returned_symbols]

        if query.symbol and missing_symbols:
            warn(f"No data was returned for: {', '.join(missing_symbols)}")

        if not query.symbol:
            df["order"] = df.groupby("period").cumcount() + 1
            df["table"] = (
                f"STEO - {table.replace('0', '') if table[0] == '0' else table}: {SteoTableNames[table]}"
            )
        records = df.to_dict(orient="records")

        return [EiaShortTermEnergyOutlookData.model_validate(d) for d in records]