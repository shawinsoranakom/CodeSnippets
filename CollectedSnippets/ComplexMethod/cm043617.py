def transform_data(
        query: FredManufacturingOutlookNYQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> AnnotatedResult[list[FredManufacturingOutlookNYData]]:
        """Transform data."""
        # pylint: disable=import-outside-toplevel
        from numpy import nan
        from pandas import Categorical, DataFrame

        df = DataFrame(data.get("data", []))

        if df.empty:
            raise EmptyDataError(
                "The request was returned empty."
                + " You may be experiencing rate limiting from the FRED API."
                + " Please try again later and reduce the number of topics selected."
            )

        metadata = data.get("metadata", {})
        df = df.melt(id_vars="date", var_name="symbol", value_name="value").query(
            "value.notnull()"
        )
        df["topic"] = df.symbol.map(ID_TO_TOPIC)
        df["field"] = df["symbol"].map(ID_TO_FIELD)

        df = df.pivot(
            columns="field", index=["date", "topic"], values="value"
        ).reset_index()
        topic_categories = [
            d for d in NY_MANUFACTURING_OUTLOOK if d in df["topic"].unique()
        ]
        df = df.replace(nan, None)

        df["topic"] = Categorical(
            df["topic"],
            categories=topic_categories,
            ordered=True,
        )
        df.sort_values(["date", "topic"], inplace=True)

        for col in df.columns:
            if col in [
                "percent_reporting_increase",
                "percent_reporting_decrease",
                "percent_reporting_no_change",
            ]:
                df[col] = df[col] / 100

        if query.transform in ["pch", "pc1", "pca", "cch", "cca"]:
            df.diffusion_index = df.diffusion_index / 100

        records = df.to_dict(orient="records")

        return AnnotatedResult(
            result=[FredManufacturingOutlookNYData.model_validate(r) for r in records],
            metadata=metadata,
        )