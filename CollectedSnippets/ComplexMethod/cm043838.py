def transform_data(
        query: TiingoCryptoHistoricalQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[TiingoCryptoHistoricalData]:
        """Return the transformed data."""
        # pylint: disable=import-outside-toplevel
        from pandas import to_datetime

        results: list[TiingoCryptoHistoricalData] = []
        symbols = query.symbol.split(",")
        returned_symbols = [item.get("ticker", "").upper() for item in data]

        for symbol in symbols:
            if symbol not in returned_symbols:
                warn(f"No data found for {symbol}")

        for item in data:
            symbol = item.get("ticker", "").upper()
            price_data = item.get("priceData", [])

            if not price_data:
                warn(f"No data found for {symbol}")
                continue

            for row in price_data:
                if len(returned_symbols) > 1:
                    row["symbol"] = symbol
                if query.interval.endswith("d"):
                    row["date"] = to_datetime(row["date"]).date()
                else:
                    row["date"] = to_datetime(row["date"], utc=True)

                results.append(TiingoCryptoHistoricalData.model_validate(row))

        return sorted(results, key=lambda x: x.date)