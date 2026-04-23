async def aextract_data(
        query: YFinanceEquityScreenerQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the raw data."""
        # pylint: disable=import-outside-toplevel
        from openbb_yfinance.utils.helpers import get_custom_screener

        operands: list = []

        if query.exchange is not None:
            operands.append(
                {"operator": "eq", "operands": ["exchange", query.exchange.upper()]},
            )
            query.country = "all"

        if query.country and query.country != "all":
            operands.append({"operator": "EQ", "operands": ["region", query.country]})

        if query.sector is not None:
            sector = SECTOR_MAP[query.sector]
            operands.append({"operator": "EQ", "operands": ["sector", sector]})

        if query.industry is not None:
            sector = (
                query.sector
                if query.sector is not None
                else get_industry_sector(query.industry)
            )
            industry = INDUSTRY_MAP[sector][query.industry]
            if industry in PEER_GROUPS:
                operands.append(
                    {"operator": "EQ", "operands": ["peer_group", industry]},
                )
            else:
                operands.append({"operator": "EQ", "operands": ["industry", industry]})

        if query.mktcap_min is not None:
            operands.append(
                {"operator": "gt", "operands": ["intradaymarketcap", query.mktcap_min]},
            )

        if query.mktcap_max is not None:
            operands.append(
                {"operator": "lt", "operands": ["intradaymarketcap", query.mktcap_max]},
            )

        if query.price_min is not None:
            operands.append(
                {"operator": "gt", "operands": ["intradayprice", query.price_min]},
            )

        if query.price_max is not None:
            operands.append(
                {"operator": "lt", "operands": ["intradayprice", query.price_max]},
            )

        if query.volume_min is not None:
            operands.append(
                {"operator": "gt", "operands": ["dayvolume", query.volume_min]},
            )

        if query.volume_max is not None:
            operands.append(
                {"operator": "lt", "operands": ["dayvolume", query.volume_max]},
            )

        if query.beta_min is not None:
            operands.append({"operator": "gt", "operands": ["beta", query.beta_min]})

        if query.beta_max is not None:
            operands.append({"operator": "lt", "operands": ["beta", query.beta_max]})

        payload = {
            "offset": 0,
            "size": 100,
            "sortField": "percentchange",
            "sortType": "DESC",
            "quoteType": "EQUITY",
            "query": {
                "operands": operands,
                "operator": "AND",
            },
            "userId": "",
            "userIdType": "guid",
        }

        response = await get_custom_screener(
            body=payload,
            limit=query.limit if query.limit and query.limit not in (0, None) else None,
        )

        if not response:
            raise EmptyDataError("No results found for the combination of filters.")

        return response