def transform_data(
        query: FederalReservePrimaryDealerFailsQueryParams,
        data: list[dict],
        **kwargs: Any,
    ) -> list[FederalReservePrimaryDealerFailsData]:
        """Transform the raw data into the standard format."""
        # pylint: disable=import-outside-toplevel
        from pandas import NA, DataFrame, concat, to_datetime

        if not data:
            raise EmptyDataError("No data returned from the Federal Reserve API.")

        df = DataFrame(data)
        df["title"] = df.keyid.map(FAILS_SERIES_TO_TITLE)
        df["value"] = df.value.astype(int)
        new_df = df.pivot(index="asofdate", columns="title", values="value").copy()
        new_data = new_df.copy()
        combined_df = DataFrame()

        for target in ["FTD", "FTR"]:
            total_col = target + " Total"
            new_data = new_df[[d for d in new_df.columns if target in d]].copy()
            new_data.loc[:, total_col] = new_data.sum(axis=1)

            if query.unit == "percent":
                new_data = new_data.div(new_data[total_col], axis=0)

            combined_df = (
                new_data.copy()
                if combined_df.empty
                else concat([combined_df, new_data], axis=1)
            )
        new_data = combined_df

        if query.asset_class == "agency":
            new_data = new_data[[d for d in new_data.columns if "Ex-MBS" in d]]
        if query.asset_class == "mbs":
            new_data = new_data[
                [d for d in new_data.columns if "MBS" in d and "Ex-MBS" not in d]
            ]
        if query.asset_class == "treasuries":
            new_data = new_data[
                [d for d in new_data.columns if "Treasury Securities (Ex-TIPS)" in d]
            ]
        if query.asset_class == "tips":
            new_data = new_data[
                [d for d in new_data.columns if "TIPS" in d and "Ex-TIPS" not in d]
            ]
        if query.asset_class == "corporate":
            new_data = new_data[[d for d in new_data.columns if "Corporate" in d]]

        new_data = new_data.T.unstack().reset_index()
        new_data.columns = ["date", "title", "value"]
        new_data["symbol"] = new_data.title.map(
            {v: k for k, v in FAILS_SERIES_TO_TITLE.items()}
        ).replace({NA: "--"})
        new_data = new_data.dropna()

        if query.unit == "value":
            new_data["value"] = new_data.value.astype(int)

        new_data["date"] = to_datetime(new_data.date).dt.date

        if query.start_date:
            new_data = new_data[new_data.date >= query.start_date]

        if query.end_date:
            new_data = new_data[new_data.date <= query.end_date]

        return [
            FederalReservePrimaryDealerFailsData.model_validate(r)
            for r in new_data.dropna().to_dict(orient="records")
        ]