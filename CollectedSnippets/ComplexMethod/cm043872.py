def extract_data(
        query: BlsSearchQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_bls.utils.helpers import open_asset
        from pandas import Series

        try:
            df = open_asset(f"{query.category}_series")
        except OpenBBError as e:
            raise e from e

        terms = [term.strip() for term in query.query.split(";")] if query.query else []

        if not terms:
            records = (
                df.to_dict(orient="records")
                if query.include_extras is True
                else df.filter(
                    items=["series_id", "series_title", "survey_name"], axis=1
                ).to_dict(orient="records")
            )
        else:
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

            records = (
                matches.to_dict(orient="records")
                if query.include_extras is True
                else matches.filter(
                    items=["series_id", "series_title", "survey_name"], axis=1
                ).to_dict(orient="records")
            )

        return records