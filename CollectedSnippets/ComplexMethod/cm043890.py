def transform_data(
        query: ImfPortInfoQueryParams,
        data: list,
        **kwargs: Any,
    ) -> list[ImfPortInfoData]:
        """Transform the raw data into a list of ImfPortInfoData."""
        results: list[ImfPortInfoData] = []

        if query.country:
            results.extend(
                [
                    ImfPortInfoData(**d["attributes"])
                    for d in sorted(
                        data,
                        key=lambda x: x["attributes"]["vessel_count_total"],
                        reverse=True,
                    )
                    if d["attributes"]["ISO3"] == query.country.upper()
                ]
            )
            if query.limit:
                results = results[: query.limit]
        elif query.continent:
            target_continent: str = ""
            for continent in PORT_CONTINENTS:
                if continent["value"] == query.continent:
                    target_continent = continent["label"]
                    break
            if target_continent:
                results.extend(
                    [
                        ImfPortInfoData(**d["attributes"])
                        for d in sorted(
                            data,
                            key=lambda x: x["attributes"]["vessel_count_total"],
                            reverse=True,
                        )
                        if d["attributes"]["continent"] == target_continent
                    ]
                )
                if query.limit:
                    results = results[: query.limit]
        else:
            results.extend(
                [
                    ImfPortInfoData(**d["attributes"])
                    for d in sorted(
                        data,
                        key=lambda x: x["attributes"]["vessel_count_total"],
                        reverse=True,
                    )
                ]
            )
            if query.limit:
                results = results[: query.limit]

        return results