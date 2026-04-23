async def aextract_data(
        query: FredTipsYieldsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> dict:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_fred.models.search import FredSearchFetcher
        from openbb_fred.models.series import FredSeriesFetcher
        from pandas import DataFrame, to_datetime

        # We get the series IDs because they will change over time.
        async def get_tips_series():
            """Get series IDs for the TIPS."""
            fetcher = FredSearchFetcher()
            res = await fetcher.fetch_data(
                params={"release_id": 72}, credentials=credentials
            )
            df = DataFrame([d.model_dump() for d in res])  # type: ignore
            df = df.query("not title.str.contains('DISCONTINUED')").set_index(
                "series_id"
            )

            df["due"] = df.title.apply(lambda x: x.split("Due ")[-1].strip()).apply(
                to_datetime
            )
            df = df[["due", "observation_start", "observation_end", "title"]]
            return df.sort_values(by="due").reset_index()  # type: ignore

        try:
            ids_df = await get_tips_series()
            ids = ids_df.series_id.to_list()
        except Exception as e:
            raise OpenBBError(e) from e

        # If we are looking for a specific tenor, the request will be smaller.
        if query.maturity:
            ids = [
                i
                for i in ids
                if i.rsplit("DTP", maxsplit=1)[-1].startswith(str(query.maturity))
            ]
        # We split the due date from the title so that we can format it as a datetime.date object.
        due_map = ids_df.set_index("series_id")["due"].dt.date.to_dict()
        # We make a seriesID-title map for later.
        title_map = (
            ids_df.set_index("series_id")["title"]
            .str.replace("Treasury Inflation-Indexed", "TIPS")
            .str.replace("  ", " ")
            .str.strip()
            .to_dict()
        )

        params = {
            k: v
            for k, v in {
                "symbol": ",".join(ids),
                "start_date": query.start_date,
                "end_date": query.end_date,
                "frequency": query.frequency,
                "aggregation_method": query.aggregation_method,
                "transform": query.transform,
            }.items()
            if v is not None
        }

        try:
            fetcher = FredSeriesFetcher()
            res = await fetcher.fetch_data(params=params, credentials=credentials)
            df = DataFrame([d.model_dump() for d in res.result])  # type: ignore
            meta: dict = res.metadata or {}  # type: ignore
        except Exception as e:
            raise OpenBBError(e) from e

        for k, v in title_map.items():
            if k in meta:
                meta[k]["title"] = v

        # We flatten the data and format the output with the metadata.

        df = (
            df.melt(
                id_vars="date",
                value_vars=[d for d in df.columns if d != "date"],
                var_name="symbol",
            )
            .dropna()
            .sort_values(by="date")
        )
        df = df.reset_index(drop=True)
        df["due"] = df.symbol.map(due_map)
        df["name"] = df.symbol.map(title_map)
        df["value"] = df["value"] / 100
        df = df[["date", "due", "symbol", "name", "value"]]
        df = df.sort_values(by=["date", "due"])  # type: ignore
        records = df.to_dict(orient="records")
        output = {
            "records": records,
            "meta": meta,
        }

        return output