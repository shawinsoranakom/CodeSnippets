async def aextract_data(
        query: FMPMarketSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_fmp.utils.helpers import get_data_many

        api_key = credentials.get("fmp_api_key") if credentials else ""
        base_url = "https://financialmodelingprep.com/stable/batch-"
        market = query.market.upper()

        if market == "ETF":
            url = f"{base_url}etf-quotes?short=false&apikey={api_key}"
        elif market == "MUTUAL_FUND":
            url = f"{base_url}mutualfund-quotes?short=false&apikey={api_key}"
        elif market == "FOREX":
            url = f"{base_url}forex-quotes?short=false&apikey={api_key}"
        elif market == "CRYPTO":
            url = f"{base_url}crypto-quotes?short=false&apikey={api_key}"
        elif market == "INDEX":
            url = f"{base_url}index-quotes?short=false&apikey={api_key}"
        elif market == "COMMODITY":
            url = f"{base_url}commodity-quotes?short=false&apikey={api_key}"
        else:
            url = f"{base_url}exchange-quote?exchange={market}&short=false&apikey={api_key}"

        return await get_data_many(url, **kwargs)