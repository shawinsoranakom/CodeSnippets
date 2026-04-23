async def aextract_data(
        query: FMPEquityScreenerQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the FMP endpoint."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import get_querystring
        from openbb_fmp.utils.helpers import get_data

        api_key = credentials.get("fmp_api_key") if credentials else ""
        sector: str = (
            query.sector.replace("_", " ").title().replace(" ", "%20")
            if query.sector
            else ""
        )
        industry_map = {v["value"]: v["label"] for v in IndustryChoices}
        industry: str = (
            industry_map.get(query.industry, query.industry) if query.industry else ""
        )
        industry = (
            industry.replace(" & ", "%20%26%20")
            .replace(" ", "%20")
            .replace("/", "%2F")
            .replace("-", "%2D")
            .replace(",", "%2C")
        )
        exchange: str = query.exchange.acronym.upper() if query.exchange else ""
        country: str = query.country.upper() if query.country else ""
        query.is_active = True if query.is_active is None else query.is_active
        query.is_etf = False if query.is_etf is None else query.is_etf
        query.is_fund = False if query.is_fund is None else query.is_fund
        query.all_share_classes = (
            False if query.all_share_classes is None else query.all_share_classes
        )

        query_dict = query.model_dump(exclude_none=True, by_alias=True)

        if sector:
            query_dict["sector"] = sector
        if industry:
            query_dict["industry"] = industry
        if exchange:
            query_dict["exchange"] = exchange
        if country:
            query_dict["country"] = country

        query_str = (
            get_querystring(query_dict, exclude=["query"])
            .replace("True", "true")
            .replace("False", "false")
        )
        base_url = "https://financialmodelingprep.com/stable/company-screener"
        url = f"{base_url}?{query_str}&apikey={api_key}"

        return await get_data(url, **kwargs)