async def aextract_data(
        query: TradierEquityQuoteQueryParams,
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
        url = f"{BASE_URL}v1/markets/quotes?symbols={query.symbol}&greeks=true"

        response = await amake_request(url, headers=HEADERS)

        if response.get("quotes"):  # type: ignore
            data = response["quotes"].get("quote")  # type: ignore
            if len(data) > 0:
                return data if isinstance(data, list) else [data]

        raise EmptyDataError("No results found.")