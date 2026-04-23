def transform_data(
        query: CboeIndexHistoricalQueryParams, data: list[dict], **kwargs: Any
    ) -> list[CboeIndexHistoricalData]:
        """Transform the data to the standard format."""
        # pylint: disable=import-outside-toplevel
        from datetime import timedelta  # noqa
        from pandas import DataFrame, Series, concat, to_datetime  # noqa

        if not data:
            raise EmptyDataError()
        results = DataFrame()
        symbols = query.symbol.split(",")
        # Results will be different depending on the interval.
        # We will also parse the output from multiple symbols.
        for i, item in enumerate(data):
            result = DataFrame()
            _symbol = symbols[i]
            _temp = item["data"]
            if query.interval == "1d":
                result = DataFrame(_temp)
                result["symbol"] = _symbol.replace("_", "").replace("^", "")
                result = result.set_index("date")
                # Remove the volume column if it exists because volume will a string 0.
                if "volume" in result.columns:
                    result = result.drop(columns="volume")
                results = concat([results, result])
            if query.interval == "1m":
                _datetime = Series([d["datetime"] for d in _temp]).rename("date")
                _price = DataFrame(d["price"] for d in _temp)
                result = _price.join(_datetime)
                result["symbol"] = _symbol.replace("_", "").replace("^", "")
                result = result.set_index("date")
                results = concat([results, result])
        results = results.set_index("symbol", append=True).sort_index()

        for c in ["open", "high", "low", "close"]:
            if c in results.columns:
                results[c] = results[c].astype(float).replace(0, None)

        output = results.dropna(how="all", axis=1).reset_index()

        # When there is only one ticker symbol, the symbol column is redundant.
        if len(query.symbol.split(",")) == 1:
            output = output.drop(columns="symbol")
        # Finally, we apply the user-specified date range because it is not filtered at the source.
        output = output[
            (to_datetime(output["date"]) >= to_datetime(query.start_date))
            & (to_datetime(output["date"]) <= to_datetime(query.end_date + timedelta(days=1)))  # type: ignore[operator]
        ]
        return [
            CboeIndexHistoricalData.model_validate(d) for d in output.to_dict("records")
        ]