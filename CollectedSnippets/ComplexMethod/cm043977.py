def transform_data(
        query: FMPHistoricalEmployeesQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FMPHistoricalEmployeesData]:
        """Return the transformed data."""
        result: list[FMPHistoricalEmployeesData] = []

        for d in data:
            if query.start_date or query.end_date:
                dt = d.get("periodOfReport")

                if not dt:
                    continue

                if query.start_date and dt < query.start_date.isoformat():
                    continue

                if query.end_date and dt > query.end_date.isoformat():
                    continue

            result.append(FMPHistoricalEmployeesData(**d))

        return sorted(result, key=lambda x: x.date, reverse=True)