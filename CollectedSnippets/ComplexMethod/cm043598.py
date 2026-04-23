def transform_data(
        query: FederalReserveTfpQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[FederalReserveTfpData]:
        """Transform the Excel data into validated Pydantic models."""
        # pylint: disable=import-outside-toplevel
        from io import BytesIO  # noqa
        import numpy as np
        import pandas as pd

        excel_file = pd.ExcelFile(BytesIO(data["file"]))
        frequency = query.frequency
        sheet_name = "quarterly" if frequency in ("quarter", "summary") else "annual"
        skiprows = 1 if sheet_name == "quarterly" else None
        df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=skiprows)
        date_col = df.columns[0]

        # Rename Excel columns to snake_case field names
        df = df.rename(columns=EXCEL_TO_FIELD)

        if sheet_name == "quarterly":
            valid_mask = df[date_col].astype(str).str.match(r"^\d{4}:Q[1-4]$")
        else:
            valid_mask = df[date_col].apply(
                lambda x: np.issubdtype(type(x), np.integer)
                or (isinstance(x, float) and x == int(x))
            )

        if frequency == "summary":
            # Summary rows are those that don't match the date pattern
            summary_df = df[~valid_mask].copy()
            summary_df = summary_df.rename(columns={date_col: "period"})
            summary_df = summary_df[summary_df["period"].isin(PERIOD_COLUMN_MAP.keys())]
            summary_df = summary_df.set_index("period").T.reset_index()
            summary_df = summary_df.rename(
                columns={"index": "variable", **PERIOD_COLUMN_MAP}
            )
            summary_df["variable_title"] = summary_df["variable"].map(VARIABLE_TITLES)
            summary_df = summary_df.replace({np.nan: None})

            results: list[FederalReserveTfpData] = [
                FederalReserveTfpData.model_validate(row.to_dict())
                for _, row in summary_df.iterrows()
            ]

            if not results:
                raise OpenBBError(
                    "No summary data found. The data source may have changed."
                )

            return results

        # Time series data
        data_df = df[valid_mask].copy()

        if frequency == "quarter":
            # Convert "YYYY:QN" to proper dates
            date_series = pd.PeriodIndex(
                data_df[date_col].str.replace(":", ""), freq="Q"
            ).to_timestamp()
            data_df[date_col] = date_series.date
        else:
            # Annual: convert year to January 1 of that year
            data_df[date_col] = pd.to_datetime(
                data_df[date_col].astype(int), format="%Y"
            ).dt.date

        data_df = data_df.rename(columns={date_col: "date"})

        # Apply date filters
        if query.start_date:
            data_df = data_df[data_df["date"] >= query.start_date]

        if query.end_date:
            data_df = data_df[data_df["date"] <= query.end_date]

        data_df = data_df.replace({np.nan: None})

        results = [
            FederalReserveTfpData.model_validate(row.to_dict())
            for _, row in data_df.iterrows()
        ]

        if not results:
            raise OpenBBError(
                "The query filters resulted in no data. "
                "Try again with different date parameters."
            )

        return results