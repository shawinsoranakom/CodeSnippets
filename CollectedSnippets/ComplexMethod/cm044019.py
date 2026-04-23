def transform_data(
        query: TradierOptionsChainsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> TradierOptionsChainsData:
        """Transform and validate the data."""
        # pylint: disable = import-outside-toplevel
        from dateutil.parser import parse
        from numpy import nan
        from openbb_core.provider.utils.helpers import safe_fromtimestamp
        from pandas import DataFrame
        from pytz import timezone

        def df_apply_dates(v):
            """Validate the dates."""
            if v != 0 and v is not None and isinstance(v, int):
                v = int(v) / 1000  # milliseconds to seconds
                v = safe_fromtimestamp(v)
                v = v.replace(microsecond=0)
                v = v.astimezone(timezone("America/New_York"))
                return v
            if v is not None and isinstance(v, str):
                v = parse(v)
                v = v.replace(microsecond=0, tzinfo=timezone("UTC"))
                v = v.astimezone(timezone("America/New_York"))
                return v
            return None

        def map_exchange(v):
            """Map the exchange from a code to a name."""
            return (
                OPTIONS_EXCHANGES.get(v)
                if v in OPTIONS_EXCHANGES
                else (
                    STOCK_EXCHANGES.get(v) if v in STOCK_EXCHANGES else v if v else None
                )
            )

        output = DataFrame(data)
        for col in output:
            if col not in ["dte", "open_interest", "volume"]:
                output[col] = output[col].replace({0: None})
            elif col in ["bid_date", "ask_date", "trade_date", "updated_at"]:
                output[col] = output[col].apply(df_apply_dates)
            elif col == "change_percentage":
                output[col] = [float(d) / 100 if d else None for d in output[col]]
            elif col in ["bidexch", "askexch"]:
                output[col] = output[col].apply(map_exchange)
            else:
                continue

        output = output.replace({nan: None}).dropna(how="all", axis=1)

        return TradierOptionsChainsData.model_validate(output.to_dict(orient="list"))