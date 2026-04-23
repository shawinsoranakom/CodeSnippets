def transform_data(
        query: IntrinioOptionsSnapshotsQueryParams,
        data: "DataFrame",
        **kwargs: Any,
    ) -> list[IntrinioOptionsSnapshotsData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        import numpy as np
        from pandas import NaT, Series, to_datetime
        from pytz import timezone

        df = data
        if df.empty:
            raise OpenBBError("Empty CSV file")
        COL_MAP = {
            "CONTRACT ID": "contract_symbol",
            "OPEN INTEREST": "open_interest",
            "TRADE PRICE": "last_price",
            "TRADE SIZE": "last_size",
            "TOTAL TRADE VOLUME": "volume",
            "LAST TRADE TIMESTAMP": "last_timestamp",
            "TRADE HIGH PRICE": "high",
            "TRADE LOW PRICE": "low",
            "ASK PRICE": "ask",
            "ASK SIZE": "ask_size",
            "LAST ASK TIMESTAMP": "ask_timestamp",
            "BID PRICE": "bid",
            "BID SIZE": "bid_size",
            "LAST BID TIMESTAMP": "bid_timestamp",
            "TOTAL ASK VOLUME": "total_ask_volume",
            "ASK HIGH PRICE": "ask_high",
            "ASK LOW PRICE": "ask_low",
            "TOTAL BID VOLUME": "total_bid_volume",
            "BID HIGH PRICE": "bid_high",
            "BID LOW PRICE": "bid_low",
        }
        df = df.rename(columns=COL_MAP)
        to_drop_na = (
            ["bid_timestamp", "ask_timestamp", "last_timestamp"]
            if query.only_traded is True
            else ["bid_timestamp", "ask_timestamp"]
        )
        df = df.dropna(subset=to_drop_na + ["contract_symbol"])
        for col in ["last_timestamp", "bid_timestamp", "ask_timestamp"]:
            # Convert Unix timestamp to tz-aware datetime
            df[col] = (
                to_datetime(df[col].replace("", None).astype(float), unit="s")
                .dt.tz_localize(timezone("UTC"))
                .dt.tz_convert(timezone("America/New_York"))
                .dt.floor("s")
            )

        # Extract the underlying symbol, expiration, option type, and strike.
        symbols = Series(df["contract_symbol"].copy())
        df["underlying_symbol"] = symbols.str.extract(r"^(?P<underlying_symbol>[^_]*)")
        split_symbols = symbols.str.rsplit("_", n=1).str[-1]
        df["expiration"] = to_datetime(
            [symbol[:6] for symbol in split_symbols],
            format="%y%m%d",
        )
        df["option_type"] = split_symbols.str.extract(
            r"^\d*(?P<option_type>\D)"
        ).replace({"C": "call", "P": "put"})
        df["strike"] = [
            (
                symbol[7:].lstrip("0")[:-3] + "." + symbol[7:].lstrip("0")[-3:]
                if "." not in symbol[7:]
                else symbol[7:]
            )
            for symbol in split_symbols
        ]

        def calculate_dte(df):
            """Calculate the DTE."""
            new_df = df[
                ["expiration", "last_timestamp", "bid_timestamp", "ask_timestamp"]
            ].copy()
            conditions = [
                new_df["last_timestamp"].notna(),
                new_df["bid_timestamp"].notna(),
                new_df["ask_timestamp"].notna(),
            ]
            choices = [
                (new_df["expiration"].dt.date - new_df["last_timestamp"].dt.date)
                .apply(lambda x: x)
                .dt.days,
                (new_df["expiration"].dt.date - new_df["bid_timestamp"].dt.date)
                .apply(lambda x: x)
                .dt.days,
                (new_df["expiration"].dt.date - new_df["ask_timestamp"].dt.date)
                .apply(lambda x: x)
                .dt.days,
            ]
            new_df["dte"] = np.select(conditions, choices, default=None)
            return new_df["dte"]

        df["dte"] = calculate_dte(df)

        def apply_contract_symbol(x):
            """Construct the OCC Contract Symbol."""
            symbol = x.split("_")[0].replace("_", "")
            exp = x.rsplit("_")[-1][:6]
            cp = x.rsplit("_")[-1][6]
            strike = x.rsplit("_")[-1][7:]
            _strike = strike.split(".")
            front = "0" * (5 - len(_strike[0]))
            back = "0" * (3 - len(_strike[1]))
            strike = f"{front}{_strike[0]}{_strike[1]}{back}"
            return symbol + exp + cp + strike

        if symbols.str.contains(r"\.").any():  # noqa  # pylint: disable=W1401
            df["contract_symbol"] = df["contract_symbol"].apply(apply_contract_symbol)
        else:
            df["contract_symbol"] = symbols.str.replace("_", "")
        df = df.replace({NaT: None, np.nan: None})
        df = df.sort_values(by="volume", ascending=False)

        return [IntrinioOptionsSnapshotsData.model_validate(df.to_dict(orient="list"))]