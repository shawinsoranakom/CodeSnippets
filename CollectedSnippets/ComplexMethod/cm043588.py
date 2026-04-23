def transform_query(params: dict[str, Any]) -> YFinanceIndexHistoricalQueryParams:
        """Transform the query."""
        # pylint: disable=import-outside-toplevel
        from dateutil.relativedelta import relativedelta
        from pandas import DataFrame

        transformed_params = params
        now = datetime.now().date()

        if params.get("start_date") is None:
            transformed_params["start_date"] = now - relativedelta(years=1)

        if params.get("end_date") is None:
            transformed_params["end_date"] = now

        tickers = params.get("symbol").lower().split(",")  # type: ignore

        new_tickers = []
        for ticker in tickers:
            _ticker = ""
            indices = DataFrame(INDICES).transpose().reset_index()
            indices.columns = ["code", "name", "symbol"]

            if ticker in indices["code"].values:
                _ticker = indices[indices["code"] == ticker]["symbol"].values[0]

            if ticker.title() in indices["name"].values:
                _ticker = indices[indices["name"] == ticker.title()]["symbol"].values[0]

            if "^" + ticker.upper() in indices["symbol"].values:
                _ticker = "^" + ticker.upper()

            if ticker.upper() in indices["symbol"].values:
                _ticker = ticker.upper()

            if _ticker != "":
                new_tickers.append(_ticker)
            else:
                warn(f"Symbol Error: {ticker} is not a supported index.")

        transformed_params["symbol"] = ",".join(new_tickers)

        return YFinanceIndexHistoricalQueryParams(**params)