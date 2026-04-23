def transform_data(
        query: FMPRevenueGeographicQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FMPRevenueGeographicData]:
        """Return the transformed data."""
        if not data:
            raise EmptyDataError("The request was returned empty.")

        results: list[FMPRevenueGeographicData] = []
        # We need to flatten the data.
        for item in data:
            period_ending = item.get("date")
            fiscal_year = item.get("fiscalYear")
            fiscal_period = item.get("period")
            segment = item.get("data", {})

            for region, revenue_value in segment.items():
                if revenue_value is not None:
                    revenue = int(revenue_value) if revenue_value is not None else None
                    if revenue is not None:
                        results.append(
                            FMPRevenueGeographicData.model_validate(
                                {
                                    "period_ending": period_ending,
                                    "fiscal_year": fiscal_year,
                                    "fiscal_period": fiscal_period,
                                    "region": region.replace("Segment", "").strip(),
                                    "revenue": revenue,
                                }
                            )
                        )

        if not results:
            raise EmptyDataError("Unknown error while transforming the data.")

        return sorted(results, key=lambda x: (x.period_ending or "", x.revenue or 0))