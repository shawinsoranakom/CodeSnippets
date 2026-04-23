async def aextract_data(
        query: FREDConsumerPriceIndexQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract data."""
        frequency = "quarterly" if query.frequency == "quarter" else query.frequency

        # Convert the params to series IDs.
        all_options = all_cpi_options(query.harmonized)
        units_dict = {
            "period": "growth_previous",
            "yoy": "growth_same",
            "index": "index_2015",
        }
        units = (
            "growth_same"
            if query.transform == "period" and frequency == "annual"
            else units_dict.get(query.transform)
        )
        step_1 = [x for x in all_options if x["country"] in query.country]
        step_2 = [x for x in step_1 if x["units"] == units]
        step_3 = [x for x in step_2 if x["frequency"] == frequency]
        ids = [item["series_id"] for item in step_3]
        country_map = {item["series_id"]: item["country"] for item in step_3}
        item_query = dict(
            symbol=",".join(ids),
            start_date=query.start_date,
            end_date=query.end_date,
        )
        results: dict = {}
        temp = await FredSeriesFetcher.fetch_data(item_query, credentials)
        result = [d.model_dump() for d in temp.result]  # type: ignore
        results["metadata"] = {country_map.get(k): v for k, v in temp.metadata.items()}  # type: ignore
        results["data"] = [
            {country_map.get(k, k): v for k, v in d.items()} for d in result
        ]

        return results