def transform_data(
        query: FredCommoditySpotPricesQueryParams, data: dict, **kwargs: Any
    ) -> AnnotatedResult[list[FredCommoditySpotPricesData]]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from pandas import DataFrame

        results = data.get("result", [])

        if not results:
            raise EmptyDataError("The request was returned with no data.")

        metadata = data.get("metadata", {})
        title_map = {k: v.get("title") for k, v in metadata.items()}
        units_map = {k: v.get("units") for k, v in metadata.items()}
        df = DataFrame([d.model_dump() for d in results])
        df = (
            df.melt(
                id_vars="date",
                value_vars=[d for d in df.columns if d != "date"],
                value_name="price",
                var_name="symbol",
            )
            .dropna()
            .sort_values(by="date")
        )
        df = df.reset_index(drop=True)
        df["commodity"] = df.symbol.map(title_map)
        df["unit"] = df.symbol.map(units_map)
        records = df.to_dict(orient="records")

        return AnnotatedResult(
            result=[FredCommoditySpotPricesData.model_validate(r) for r in records],
            metadata=metadata,
        )