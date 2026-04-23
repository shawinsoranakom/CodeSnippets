def transform_data(
        query: BlsSeriesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[BlsSeriesData]]:
        """Transform the data."""
        series_data = data.get("data", [])
        messages = data.get("messages", [])
        metadata = data.get("metadata", {})
        if messages:
            for message in messages:
                warn(message)

        results = sorted(
            [BlsSeriesData.model_validate(series) for series in series_data],
            key=lambda x: (x.date, x.symbol),
        )

        if query.start_date is not None:
            results = [r for r in results if r.date >= query.start_date]

        if query.end_date is not None:
            results = [r for r in results if r.date <= query.end_date]

        return AnnotatedResult(
            result=results,
            metadata=metadata,
        )