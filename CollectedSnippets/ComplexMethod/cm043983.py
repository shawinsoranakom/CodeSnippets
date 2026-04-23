def transform_data(
        query: FMPHistoricalDividendsQueryParams, data: list, **kwargs: Any
    ) -> list[FMPHistoricalDividendsData]:
        """Return the transformed data."""
        result: list[FMPHistoricalDividendsData] = []

        for d in data:
            d["declarationDate"] = d.get("declarationDate") or None

            if query.start_date or query.end_date:
                dt = d.get("date")

                if not dt:
                    continue

                if query.start_date and dt < query.start_date.isoformat():
                    continue

                if query.end_date and dt > query.end_date.isoformat():
                    continue

            result.append(FMPHistoricalDividendsData(**d))

        return result