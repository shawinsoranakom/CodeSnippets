def transform_data(
        query: CboeEquityHistoricalQueryParams, data: list[dict], **kwargs: Any
    ) -> list[CboeEquityHistoricalData]:
        """Transform the data to the standard format."""
        # pylint: disable=import-outside-toplevel
        import contextlib  # noqa
        from datetime import timedelta  # noqa
        from pandas import DataFrame, Series, concat, to_datetime  # noqa

        if not data:
            raise EmptyDataError()
        results = DataFrame()
        # Results will be different depending on the interval.
        # We will also parse the output from multiple symbols.
        for item in data:
            result = DataFrame()
            _symbol = item["symbol"]
            _temp = item["data"]
            if query.interval == "1d":
                result = DataFrame(_temp)
                result["symbol"] = _symbol.replace("_", "").replace("^", "")
                result = result.set_index("date")
                results = concat([results, result])
            if query.interval == "1m":
                _datetime = Series([d["datetime"] for d in _temp]).rename("date")
                _price = DataFrame(d["price"] for d in _temp)
                _volume = DataFrame(d["volume"] for d in _temp)
                result = _price.join([_volume, _datetime])
                result["symbol"] = _symbol.replace("_", "").replace("^", "")
                result = result.set_index("date")
                results = concat([results, result])
        results = results.set_index("symbol", append=True).sort_index()
        # There are some bad data points in the open/high/low results that will break things.
        for c in results.columns:
            # Some symbols do not have volume data, and some intraday symbols don't have options.
            if c in ["volume", "puts_volume", "calls_volume", "total_options_volume"]:
                results[c] = results[c].astype(float).astype("int64")
                results = (
                    results.drop(columns=c)
                    if results[c].sum() == 0 and c != "volume"
                    else results
                )
            # Sub-penny prices are not warranted for any of the assets returned.
            if c in ["open", "high", "low", "close"]:
                with contextlib.suppress(Exception):
                    results[c] = results[c].astype(float)
                    results[c] = round(results[c], 2)
        output = results.dropna(how="all", axis=1).reset_index()
        output = output[output["open"] > 0]
        # When there is only one ticker symbol, the symbol column is redundant.
        if len(query.symbol.split(",")) == 1:
            output = output.drop(columns="symbol")
        # Finally, we apply the user-specified date range because it is not filtered at the source.
        output = output[
            (to_datetime(output["date"]) >= to_datetime(query.start_date))
            & (to_datetime(output["date"]) <= to_datetime(query.end_date + timedelta(days=1)))  # type: ignore[operator]
        ]
        return [
            CboeEquityHistoricalData.model_validate(d)
            for d in output.to_dict("records")
        ]