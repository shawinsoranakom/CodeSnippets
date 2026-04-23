def transform_data(
        query: FredBondIndicesQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[FredBondIndicesData]]:
        """Transform data."""
        # pylint: disable=import-outside-toplevel
        from pandas import Categorical, DataFrame

        if not data:
            raise EmptyDataError("The request was returned empty.")
        df = DataFrame.from_records(data["data"])
        if df.empty:
            raise EmptyDataError(
                "No data found for the given query. Try adjusting the parameters."
            )
        # Flatten the data as a pivot table.
        df = (
            df.melt(id_vars="date", var_name="symbol", value_name="value")
            .query("value.notnull()")
            .set_index(["date", "symbol"])
            .sort_index()
            .reset_index()
        )
        # Normalize the percent values.
        if query.index_type != "total_return":
            df["value"] = df["value"] / 100

        titles_dict = {
            symbol: data["metadata"][symbol].get("title")
            for symbol in query._symbols.split(",")  # type: ignore  # pylint: disable=protected-access
        }
        df["title"] = df.symbol.map(titles_dict)

        if query.index == "yield_curve":
            maturities_dict = BAML_CATEGORIES[query.category][query.index]  # type: ignore
            maturities = list(maturities_dict)
            maturity_dict = {
                maturities_dict[item][query.index_type]: item for item in maturities
            }
            df["maturity"] = df.symbol.map(maturity_dict)
            df["maturity"] = Categorical(
                df["maturity"],
                categories=maturities,
                ordered=True,
            )
            df = df.sort_values(by=["date", "maturity"]).reset_index(drop=True)

        records = df.to_dict(orient="records")
        metadata = data.get("metadata", {})

        return AnnotatedResult(
            result=[FredBondIndicesData.model_validate(r) for r in records],
            metadata=metadata,
        )