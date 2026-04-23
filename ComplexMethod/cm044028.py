def extract_data(
        query: NasdaqEquityScreenerQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data from the Nasdaq Equity Screener."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import get_querystring, make_request
        from openbb_nasdaq.utils.helpers import get_headers

        HEADERS = get_headers(accept_type="text")
        base_url = (
            "https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit="
            f"{query.limit or 10000}&"
        )
        exchange = query.exchange.split(",")
        exsubcategory = query.exsubcategory.split(",")
        marketcap = query.mktcap.split(",")
        recommendation = query.recommendation.split(",")
        sector = (
            query.sector.replace("communications_services", "telecommunications")
            .replace("financial_services", "finance")
            .split(",")
        )
        region = query.region.split(",")
        country = query.country.split(",")
        params = dict(
            exchange=None if "all" in exchange else "|".join(exchange).upper(),
            exsubcategory=(
                None if "all" in exsubcategory else "|".join(exsubcategory).upper()
            ),
            marketcap=None if "all" in marketcap else "|".join(marketcap),
            recommendation=(
                None if "all" in recommendation else "|".join(recommendation)
            ),
            sector=None if "all" in sector else "|".join(sector),
            region=None if "all" in region else "|".join(region),
            country=None if "all" in country else "|".join(country),
        )
        querystring = get_querystring(params, [])
        querystring = "&" + querystring if querystring else ""
        url = f"{base_url}{querystring}"
        try:
            response = make_request(url, headers=HEADERS)
            return response.json()
        except Exception as error:
            raise OpenBBError(f"Failed to get data from Nasdaq -> {error}") from error