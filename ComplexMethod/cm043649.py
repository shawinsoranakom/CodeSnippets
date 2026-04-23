def transform_data(
        query: IntrinioForwardEpsEstimatesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[IntrinioForwardEpsEstimatesData]:
        """Transform the raw data into the standard format."""
        symbols = query.symbol.split(",") if query.symbol else []
        results: list[IntrinioForwardEpsEstimatesData] = []
        for item in sorted(
            data,
            key=lambda item: (  # type: ignore
                (
                    symbols.index(item.get("symbol")) if item.get("symbol") in symbols else len(symbols),  # type: ignore
                    item.get("date"),
                )
                if symbols
                else item.get("date")
            ),
        ):
            temp: dict[str, Any] = {}
            company = item.pop("company")
            if company.get("ticker") is None:
                continue
            temp["symbol"] = company.get("ticker")
            temp["name"] = company.get("name")
            if query.fiscal_period and query.fiscal_period.upper() != item.get(
                "fiscal_period"
            ):
                continue
            if query.calendar_period and query.calendar_period.upper() != item.get(
                "calendar_period"
            ):
                continue
            temp.update(item)
            results.append(IntrinioForwardEpsEstimatesData.model_validate(temp))

        return results