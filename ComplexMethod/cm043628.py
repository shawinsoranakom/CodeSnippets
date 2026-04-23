def transform_data(
        query: FredSearchQueryParams, data: list[dict], **kwargs: Any
    ) -> list[FredSearchData]:
        """Transform data."""
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import DataFrame, Series

        if not data:
            raise EmptyDataError("The request was returned empty.")

        df = DataFrame(data)

        if query.search_type == "release" and query.release_id is None:
            df = df.rename(columns={"id": "release_id"})

        terms = [term.strip() for term in query.query.split(";")] if query.query else []
        tags = (
            [tag.strip() for tag in query.tag_names.split(";")]
            if query.tag_names and query.search_type != "series_id"
            else []
        )
        terms += tags

        if terms and query.search_type != "series_id":
            combined_mask = Series([True] * len(df))
            for term in terms:
                mask = df.apply(
                    lambda row, term=term: row.astype(str).str.contains(
                        term, case=False, regex=True, na=False
                    )
                ).any(axis=1)
                combined_mask &= mask

            matches = df[combined_mask]

            if matches.empty:
                raise EmptyDataError("No results found for the provided query.")

            df = matches

        df = df.replace({nan: None})

        if query.order_by in df.columns:
            df = df.sort_values(
                by=query.order_by, ascending=query.sort_order == "asc"
            ).reset_index(drop=True)

        if "series_group" in df.columns:
            df.series_group = df.series_group.astype(str)

        if "release_id" in df.columns:
            df.release_id = df.release_id.astype(str)

        if query.limit is not None and len(df) > query.limit:
            df = df.iloc[: query.limit]

        records = df.to_dict(orient="records")

        return [FredSearchData.model_validate(r) for r in records]