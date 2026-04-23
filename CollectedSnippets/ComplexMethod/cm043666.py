def transform_data(
        query: IntrinioForwardEbitdaEstimatesQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[IntrinioForwardEbitdaEstimatesData]:
        """Transform the raw data into the standard format."""
        if not data:
            raise EmptyDataError()
        results: list[IntrinioForwardEbitdaEstimatesData] = []
        fiscal_period = None
        if query.fiscal_period is not None:
            fiscal_period = "fy" if query.fiscal_period == "annual" else "fq"
        for item in data:
            estimate_count = item.get("estimate_count")
            if (
                not estimate_count
                or estimate_count == 0
                or not item.get("updated_date")
            ):
                continue
            if fiscal_period and item.get("period") != fiscal_period:
                continue
            results.append(IntrinioForwardEbitdaEstimatesData.model_validate(item))
        if not results:
            raise EmptyDataError()

        return sorted(
            results, key=lambda x: (x.fiscal_year, x.last_updated), reverse=True
        )