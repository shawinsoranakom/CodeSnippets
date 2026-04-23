def transform_query(params: dict[str, Any]) -> YFinanceEquityScreenerQueryParams:
        """Transform query."""
        sector = params.get("sector")
        industry = params.get("industry")

        if industry and sector:
            sec = get_industry_sector(industry)
            if sec and sec != sector:
                choices = "\n    ".join(sorted(INDUSTRY_MAP[sector]))
                raise OpenBBError(
                    ValueError(
                        f"Industry {industry} does not belong to sector {sector}."
                        " Valid choices are:" + "\n\n    " + f"{choices}",
                    ),
                )
        elif industry and not sector:
            choices = "\n".join(INDUSTRIES)
            sector = get_industry_sector(industry)
            if not sector:
                raise OpenBBError(
                    ValueError(
                        f"Industry {industry} not found. Valid choices are:\n"
                        f"{choices}",
                    ),
                )
            _industry = INDUSTRY_MAP[sector][industry]

            if _industry not in PEER_GROUPS:
                params["sector"] = get_industry_sector(industry)

        return YFinanceEquityScreenerQueryParams(**params)