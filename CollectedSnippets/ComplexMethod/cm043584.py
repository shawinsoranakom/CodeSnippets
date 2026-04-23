def transform_query(params: dict[str, Any]) -> YFinanceFuturesHistoricalQueryParams:
        """Transform the query."""
        # pylint: disable=import-outside-toplevel
        from dateutil.relativedelta import relativedelta
        from openbb_yfinance.utils.helpers import get_futures_data

        transformed_params = params.copy()

        symbols = params["symbol"].split(",")
        new_symbols = []
        futures_data = get_futures_data()
        for symbol in symbols:
            if params.get("expiration"):
                expiry_date = datetime.strptime(
                    transformed_params["expiration"], "%Y-%m"
                )
                if "." not in symbol:
                    exchange = futures_data[futures_data["Ticker"] == symbol][
                        "Exchange"
                    ].values[0]
                    new_symbol = f"{symbol}{MONTHS[expiry_date.month]}{str(expiry_date.year)[-2:]}.{exchange}"
                else:
                    new_symbol = symbol
                new_symbols.append(new_symbol)
            else:
                new_symbols.append(symbol)

        formatted_symbols = []
        for s in new_symbols:
            if "." not in s.upper() and "=F" not in s.upper():
                formatted_symbols.append(f"{s.upper()}=F")
            else:
                formatted_symbols.append(s.upper())

        transformed_params["symbol"] = ",".join(formatted_symbols)

        now = datetime.now()

        if params.get("start_date") is None:
            transformed_params["start_date"] = (now - relativedelta(years=1)).strftime(
                "%Y-%m-%d"
            )

        if params.get("end_date") is None:
            transformed_params["end_date"] = now.strftime("%Y-%m-%d")

        return YFinanceFuturesHistoricalQueryParams(**transformed_params)