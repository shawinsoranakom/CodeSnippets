async def aextract_data(
        query: TradierOptionsChainsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Tradier endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import amake_request  # noqa
        from openbb_tradier.models.equity_quote import TradierEquityQuoteFetcher  # noqa

        api_key = credentials.get("tradier_api_key") if credentials else ""
        sandbox = True

        if api_key and credentials.get("tradier_account_type") not in ["sandbox", "live"]:  # type: ignore
            raise OpenBBError(
                "Invalid account type for Tradier. Must be either 'sandbox' or 'live'."
            )

        if api_key:
            sandbox = (
                credentials.get("tradier_account_type") == "sandbox"
                if credentials
                else False
            )

        BASE_URL = (
            "https://api.tradier.com/v1/markets/options/"
            if sandbox is False
            else "https://sandbox.tradier.com/v1/markets/options/"
        )

        HEADERS = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }

        # Get the expiration dates for the symbol so we can gather the chains data.
        async def get_expirations(symbol):
            """Get the expiration dates for the given symbol."""
            url = (
                f"{BASE_URL}expirations?symbol={symbol}&includeAllRoots=true"
                "&strikes=false&contractSize=false&expirationType=false"
            )
            response = await amake_request(url, headers=HEADERS)
            if response.get("expirations") and isinstance(response["expirations"].get("date"), list):  # type: ignore
                expirations = response["expirations"].get("date")  # type: ignore
                return expirations if expirations else []

        expirations = await get_expirations(query.symbol)
        if expirations == []:
            raise OpenBBError(f"No expiration dates found for {query.symbol}")

        results: list = []

        underlying_quote = await TradierEquityQuoteFetcher.fetch_data(
            {"symbol": query.symbol}, credentials
        )
        underlying_price = underlying_quote[0].last_price  # type: ignore

        async def get_one(url, underlying_price):
            """Get the chain for a single expiration."""
            chain = await amake_request(url, headers=HEADERS)
            if chain.get("options") and isinstance(chain["options"].get("option", []), list):  # type: ignore
                data = chain["options"]["option"]  # type: ignore
                for d in data.copy():
                    # Remove any strikes returned without data.
                    keys = ["last", "bid", "ask"]
                    if all(d.get(key) in [0, "0", None] for key in keys):
                        data.remove(d)
                        continue
                    # Flatten the nested greeks dictionary
                    greeks = d.pop("greeks")
                    if greeks is not None:
                        d.update(**greeks)
                    # Pop fields that are duplicate information or not of interest.
                    to_pop = [
                        "root_symbol",
                        "exch",
                        "type",
                        "expiration_type",
                        "description",
                        "average_volume",
                    ]
                    _ = [d.pop(key) for key in to_pop if key in d]
                    # Add the DTE field to the data for easier filtering later.
                    d["dte"] = (
                        datetime.strptime(d["expiration_date"], "%Y-%m-%d").date()
                        - datetime.now().date()
                    ).days
                    if underlying_price is not None:
                        d["underlying_price"] = underlying_price

                results.extend(data)

        urls = [
            f"{BASE_URL}chains?symbol={query.symbol}&expiration={expiration}&greeks=true"
            for expiration in expirations  # type: ignore
        ]

        await asyncio.gather(*[get_one(url, underlying_price) for url in urls])

        if not results:
            raise EmptyDataError(f"No options chains data found for {query.symbol}.")
        return sorted(
            results, key=lambda x: [x["expiration_date"], x["strike"], x["symbol"]]
        )