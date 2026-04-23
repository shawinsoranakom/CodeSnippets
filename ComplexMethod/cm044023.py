async def aextract_data(
        query: TradierEquitySearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Tradier endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import amake_request

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
            "https://api.tradier.com/"
            if sandbox is False
            else "https://sandbox.tradier.com/"
        )
        HEADERS = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        is_symbol = "lookup" if query.is_symbol else "search"
        url = f"{BASE_URL}v1/markets/{is_symbol}?q={query.query}"
        if is_symbol == "lookup":
            url += "&types=stock, option, etf, index"
        if is_symbol == "search":
            url += "&indexes=true"

        response = await amake_request(url, headers=HEADERS)

        if response.get("securities"):  # type: ignore
            data = response["securities"].get("security")  # type: ignore
            if len(data) > 0:
                return data if isinstance(data, list) else [data]

        raise EmptyDataError("No results found.")