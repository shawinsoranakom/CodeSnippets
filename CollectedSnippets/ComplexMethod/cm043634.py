async def aextract_data(
        query: FredNonFarmPayrollsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import amake_request
        from numpy import nan
        from pandas import DataFrame, to_datetime

        api_key = credentials.get("fred_api_key") if credentials else ""
        element_id = EstablishmentData[query.category]
        dates: list = [""]

        if query.date:
            if query.date and isinstance(query.date, dateType):
                query.date = query.date.strftime("%Y-%m-%d")
            dates = query.date.split(",")  # type: ignore
            dates = [d.replace(d[-2:], "01") if len(d) == 10 else d for d in dates]
            dates = list(set(dates))
            dates = [f"&observation_date={date}" for date in dates if date] if dates else ""  # type: ignore

        URLS = [
            f"https://api.stlouisfed.org/fred/release/tables?release_id=50&element_id={element_id}"
            + f"{date}&include_observation_values=true&api_key={api_key}"
            + "&file_type=json"
            for date in dates
        ]
        results: list = []

        async def get_one(URL):
            """Get the observations for a single date."""
            response = await amake_request(URL)
            data = [v for v in response.get("elements", {}).values() if v.get("observation_value") != "."]  # type: ignore
            if data:
                df = (
                    DataFrame(data)
                    .set_index(["element_id", "parent_id"])
                    .sort_index()[
                        [
                            "level",
                            "series_id",
                            "name",
                            "observation_date",
                            "observation_value",
                        ]
                    ]
                    .reset_index()
                )
                df["parent_id"] = df.parent_id.astype(str)
                df["element_id"] = df.element_id.astype(str)
                df["observation_value"] = df.observation_value.str.replace(
                    ",", ""
                ).astype(float)
                if query.category.startswith(
                    "employees"
                ) and not query.category.endswith("percent"):
                    df["observation_value"] = df.observation_value * 1000
                elif query.category.endswith("percent"):
                    df["observation_value"] = df.observation_value / 100

                df["observation_date"] = to_datetime(
                    df["observation_date"], format="%b %Y"
                ).dt.date
                children = (
                    df.groupby("parent_id")["element_id"]
                    .apply(lambda x: x.sort_values().unique().tolist())
                    .to_dict()
                )
                children = {k: ",".join(v) for k, v in children.items()}
                df["children"] = df.element_id.map(children)
                df = (
                    df.set_index(["element_id", "children", "parent_id", "level"])
                    .sort_index()
                    .reset_index()
                    .replace({nan: None})
                )
                results.extend(df.to_dict("records"))

        await asyncio.gather(*[get_one(URL) for URL in URLS])

        return results