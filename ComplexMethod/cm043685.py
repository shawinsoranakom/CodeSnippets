def transform_data(
        query: TmxBondPricesQueryParams,
        data: "DataFrame",
        **kwargs: Any,
    ) -> list[TmxBondPricesData]:
        """Transform data."""
        # pylint: disable=import-outside-toplevel
        from numpy import nan

        bonds = data.copy()

        if query.isin is not None:
            isin_list = (
                query.isin.split(",") if isinstance(query.isin, str) else query.isin
            )

            data = bonds[
                bonds["isin"].str.contains("|".join(isin_list), na=False, case=False)
            ].query("bondType == 'Corp'")

            if data.empty or len(data) == 0:
                raise OpenBBError(
                    f"No bonds found for the provided ISIN(s) -> {', '.join(isin_list)}",
                )
        else:
            data = bonds.query(
                "bondType == 'Corp'& maturityDate >= @query.maturity_date_min.strftime('%Y-%m-%d')"
            ).sort_values(by=["maturityDate"])

        data["issuer"] = data.issuer.str.strip()

        if query.maturity_date_max:
            data = data.query(
                "maturityDate <= @query.maturity_date_max.strftime('%Y-%m-%d')"
            )
        if query.last_traded_min:
            data = data.query(
                "lastTradedDate >= @query.last_traded_min.strftime('%Y-%m-%d')"
            )
        if query.coupon_min:
            data = data.query("couponRate >= @query.coupon_min")
        if query.coupon_max:
            data = data.query("couponRate <= @query.coupon_max")
        if query.issuer_name:
            data = data.query("issuer.str.contains(@query.issuer_name, case=False)")

        if len(data) > 0:
            data = data.drop(columns=["bondType", "securityId", "secKey"])
            data = data.replace({nan: None})
        else:
            raise OpenBBError(
                "No bonds found for the provided query parameters.",
            )

        return [TmxBondPricesData.model_validate(d) for d in data.to_dict("records")]