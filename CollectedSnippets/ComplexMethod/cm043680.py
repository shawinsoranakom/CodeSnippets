async def aextract_data(
        query: TmxIndexSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the TMX endpoint."""
        # pylint: disable=import-outside-toplevel
        import json  # noqa
        from openbb_tmx.utils import gql  # noqa
        from openbb_tmx.utils.helpers import (  # noqa
            NASDAQ_GIDS,
            get_data_from_gql,
            get_data_from_url,
            get_random_agent,
            get_indices_backend,
        )

        url = "https://tmxinfoservices.com/files/indices/sptsx-indices.json"
        user_agent = get_random_agent()
        results = []
        if query.region == "ca":
            data = await get_data_from_url(
                url,
                use_cache=query.use_cache,
                backend=get_indices_backend(),
            )
            if not data:
                raise EmptyDataError
            symbols = []

            for symbol in data["indices"]:
                symbols.append(symbol)
                new_data = {}
                performance = data["indices"][symbol].get("performance", {})
                market_value = data["indices"][symbol].get("quotedmarketvalue", {})
                new_data.update(
                    {
                        "symbol": symbol,
                        "name": data["indices"][symbol].get("name_en", None),
                        "currency": (
                            "USD"
                            if "(USD)" in data["indices"][symbol]["name_en"]
                            else "CAD"
                        ),
                        **performance,
                        **market_value,
                    }
                )
                results.append(new_data)

            # Get current levels for each index.

            payload = gql.get_quote_for_symbols_payload.copy()
            payload["variables"]["symbols"] = symbols

            url = "https://app-money.tmx.com/graphql"
            response = await get_data_from_gql(
                method="POST",
                url=url,
                data=json.dumps(payload),
                headers={
                    "authority": "app-money.tmx.com",
                    "referer": "https://money.tmx.com/en/quote/^TSX",
                    "locale": "en",
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Accept": "*/*",
                },
                timeout=5,
            )
            if response.get("data") and response["data"].get("getQuoteForSymbols"):
                quote_data = response["data"]["getQuoteForSymbols"]
                for d in data:
                    if "longname" in d:
                        d.pop("longname")
                    if "percentChange" in d:
                        d.pop("percentChange")
                merged_list = [
                    {
                        **d1,
                        **next(
                            (d2 for d2 in quote_data if d2["symbol"] == d1["symbol"]),
                            {},
                        ),
                    }
                    for d1 in results
                ]
                results = merged_list

        if query.region == "us":
            symbols = [f"{symbol}:US" for symbol in NASDAQ_GIDS]
            payload = gql.get_quote_for_symbols_payload.copy()
            payload["variables"]["symbols"] = symbols

            url = "https://app-money.tmx.com/graphql"
            response = await get_data_from_gql(
                method="POST",
                url=url,
                data=json.dumps(payload),
                headers={
                    "authority": "app-money.tmx.com",
                    "referer": "https://money.tmx.com/en/quote/^TSX",
                    "locale": "en",
                    "Content-Type": "application/json",
                    "User-Agent": user_agent,
                    "Accept": "*/*",
                },
                timeout=5,
            )
            if response.get("data") and response["data"].get("getQuoteForSymbols"):
                results = response["data"]["getQuoteForSymbols"]
            for item in results:
                item["change_percent"] = item.pop("percentChange")

        return results