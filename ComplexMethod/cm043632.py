def transform_data(
        query: FredRegionalQueryParams,
        data: dict,
        **kwargs,
    ) -> AnnotatedResult[list[FredRegionalData]]:
        """Flatten the response object and validate the model."""
        results: list[FredRegionalData] = []
        if data.get("meta") is None:
            raise EmptyDataError()
        meta = {k: v for k, v in data.get("meta").items() if k not in ["data"]}  # type: ignore
        _data = data["meta"]["data"]
        keys = list(_data.keys())
        units = data["meta"].get("units")
        for key in keys:
            _row = _data[key]
            for item in _row:
                item["date"] = key
                item["units"] = units
                if (
                    query.end_date is None
                    or datetime.strptime(key, "%Y-%m-%d").date() <= query.end_date
                ):
                    results.append(FredRegionalData.model_validate(item))

        return AnnotatedResult(result=results, metadata=meta)