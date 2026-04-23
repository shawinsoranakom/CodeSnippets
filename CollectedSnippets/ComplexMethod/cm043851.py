def transform_data(
        query: FamaFrenchInternationalIndexReturnsQueryParams,
        data: tuple,
        **kwargs: Any,
    ) -> AnnotatedResult[list[FamaFrenchInternationalIndexReturnsData]]:
        """Transform the extracted data."""
        # pylint: disable=import-outside-toplevel
        from pandas import MultiIndex

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
                    if query.measure == "ratios" and col == "firms"
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

        if isinstance(returns_data.columns, MultiIndex):
            returns_data.columns = [
                " ".join([str(level) for level in col if str(level) != ""])
                for col in returns_data.columns.values
            ]

        metadata = meta[0] if isinstance(meta, list) else meta
        description = metadata.pop("description", "")
        new_description = """
We form value and growth portfolios in each country using four ratios:

- book-to-market (B/M)
- earnings-price (E/P)
- cash earnings to price (CE/P)
- dividend yield (D/P)

The returns on the index portfolios are constructed by averaging the returns on the country portfolios.
Each country is added to the index portfolios when the return data for the country begin;
the country start dates can be inferred from the country return files.

We weight countries in the index portfolios in proportion to their EAFE + Canada weights.

The raw data are from Morgan Stanley Capital International for 1975 to 2006 and from
Bloomberg for 2007 to present.
        """
        metadata["description"] = "### " + description + "\n" + new_description

        return AnnotatedResult(
            result=[
                FamaFrenchInternationalIndexReturnsData(**d)
                for d in returns_data.reset_index().to_dict(orient="records")
            ],
            metadata=meta[0] if isinstance(meta, list) else meta,
        )