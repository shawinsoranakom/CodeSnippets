def transform_data(
        query: TmxEquityHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[TmxEquityHistoricalData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame, to_datetime

        results = DataFrame(data)
        if results.empty or len(results) == 0:
            raise EmptyDataError()

        # Handle the date formatting differences.
        results = results.rename(columns={"dateTime": "datetime"})
        if query.interval != "day":
            results["datetime"] = to_datetime(results["datetime"], utc=True)
            if query.interval in ("week", "month"):
                results["datetime"] = results["datetime"].dt.strftime("%Y-%m-%d")
            else:
                results["datetime"] = results["datetime"].dt.strftime(
                    "%Y-%m-%d %H:%M:%S%z"
                )
        if query.interval == "day":
            results["datetime"] = to_datetime(results["datetime"]).dt.strftime(
                "%Y-%m-%d"
            )

        symbols = query.symbol.split(",")
        # If there are multiple symbols, sort the data by datetime and symbol.
        if len(symbols) > 1:
            results = results.set_index(["datetime", "symbol"]).sort_index()
            results = results.reset_index()
        # If there is only one symbol, drop the symbol column.
        if len(symbols) == 1:
            results = results.drop(columns=["symbol"])
        # Normalizes the percent change values.
        if "changePercent" in results.columns:
            results["changePercent"] = results["changePercent"].astype(float) / 100
        # For the week beginning 2011-09-12 replace the openPrice NaN with 0 because of 9/11.
        if query.interval == "week":
            results["open"] = results["open"].fillna(0)
        # Convert any NaN values to None.
        results = results.fillna(value="N/A").replace("N/A", None)

        return [
            TmxEquityHistoricalData.model_validate(d)
            for d in results.to_dict("records")
        ]