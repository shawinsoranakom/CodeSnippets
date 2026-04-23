def transform_data(
        query: TradierEquityQuoteQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[TradierEquityQuoteData]:
        """Transform and validate the data."""
        results: list[TradierEquityQuoteData] = []

        for d in data:
            d["exch"] = (
                OPTIONS_EXCHANGES.get(d["exch"])
                if d.get("type") in ["option", "index"]
                else STOCK_EXCHANGES.get(d["exch"])
            )
            d["askexch"] = (
                OPTIONS_EXCHANGES.get(d["askexch"])
                if d.get("type") in ["option", "index"]
                else STOCK_EXCHANGES.get(d["askexch"])
            )
            d["bidexch"] = (
                OPTIONS_EXCHANGES.get(d["bidexch"])
                if d.get("type") in ["option", "index"]
                else STOCK_EXCHANGES.get(d["bidexch"])
            )

            if "greeks" in d:
                # Flatten the nested greeks dictionary
                greeks = d.pop("greeks")
                if greeks is not None:
                    d.update(**greeks)

            if (
                d.get("root_symbols") == d.get("symbol")
                and d.get("root_symbols") is not None
            ):
                _ = d.pop("root_symbols")

            if (
                d.get("root_symbol") == d.get("underlying")
                and d.get("root_symbol") is not None
            ):
                _ = d.pop("root_symbol")

            results.append(TradierEquityQuoteData.model_validate(d))

        return results