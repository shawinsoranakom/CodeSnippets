def transform_data(
        query: FamaFrenchRegionalPortfolioReturnsQueryParams,
        data: tuple,
        **kwargs: Any,
    ) -> AnnotatedResult[list[FamaFrenchRegionalPortfolioReturnsData]]:
        """Transform the extracted data."""
        dfs, meta = data

        if not dfs:
            raise OpenBBError(
                "The request was returned empty."
                + " This may be due to an invalid, or incorrectly mapped, portfolio choice."
            )
        returns_data = dfs[0] if isinstance(dfs, list) else dfs

        # Values of -99.99  or -999 indicate no data,
        # Drop columns that have no data.
        for col in returns_data.columns:
            if all(returns_data[col].values == "-99.99") or all(
                returns_data[col].values == "-999"
            ):
                returns_data = returns_data.drop(columns=[col])
            else:
                returns_data[col] = (
                    returns_data[col].astype(int)
                    if query.measure == "number_of_firms"
                    else returns_data[col].astype(float)
                )

        if query.start_date:
            returns_data = returns_data[
                returns_data.index >= query.start_date.strftime("%Y-%m-%d")
            ]

        if query.end_date:
            returns_data = returns_data[
                returns_data.index <= query.end_date.strftime("%Y-%m-%d")
            ]

        # Flatten the DataFrame to conform to the Data model
        # This avoids having undefined fields.
        flattened_data = (
            returns_data.reset_index()
            .melt(
                id_vars=["Date"],
                var_name="portfolio",
                value_name="value",
            )
            .copy()
        )
        flattened_data["measure"] = query.measure

        return AnnotatedResult(
            result=[
                FamaFrenchRegionalPortfolioReturnsData(**d)
                for d in flattened_data.to_dict(orient="records")
            ],
            metadata=meta[0] if isinstance(meta, list) else meta,
        )