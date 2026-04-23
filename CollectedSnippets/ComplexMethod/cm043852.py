def transform_data(
        query: FamaFrenchCountryPortfolioReturnsQueryParams,
        data: tuple,
        **kwargs: Any,
    ) -> AnnotatedResult[list[FamaFrenchCountryPortfolioReturnsData]]:
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

We form the portfolios at the end of December each year by sorting on one of the four ratios
and then compute value-weighted returns for the following 12 months.

The value portfolios (High) contain firms in the top 30% of a ratio
and the growth portfolios (Low) contain firms in the bottom 30%.

There are two sets of portfolios. In one, firms are included only if we have data on all four ratios.
In the other, a firm is included in a sort variable's portfolios if we have data for that variable.

The market return (Mkt) for the first set is the value weighted average of the returns
for only firms with all four ratios.
The market return for the second set includes all firms with book-to-market data,
and Firms is the number of firms with B/M data.

The raw data are from Morgan Stanley Capital International for 1975 to 2006 and from
Bloomberg for 2007 to present.
        """
        metadata["description"] = "### " + description + "\n\n" + new_description

        return AnnotatedResult(
            result=[
                FamaFrenchCountryPortfolioReturnsData(**d)
                for d in returns_data.reset_index().to_dict(orient="records")
            ],
            metadata=meta[0] if isinstance(meta, list) else meta,
        )