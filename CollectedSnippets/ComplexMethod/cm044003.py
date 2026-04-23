def transform_data(
        query: EconDbPortVolumeQueryParams,
        data: dict,
        **kwargs: Any,
    ) -> list[EconDbPortVolumeData]:
        """Transform the data."""
        # pylint: disable=import-outside-toplevel
        from openbb_econdb.utils.helpers import COUNTRY_MAP
        from pandas import DataFrame, concat, to_datetime

        df: DataFrame = DataFrame()
        res = data.copy()

        if not res:
            raise EmptyDataError("The request was returned empty.")

        ports = res.pop("Ports", None)
        code_to_city_map = {d["locode"]: d["name"] for d in ports}
        code_to_country_map = {d["locode"]: d["iso2"] for d in ports}
        port_codes = list(code_to_city_map)

        for code in port_codes:
            new_data: list = []
            for k, v in res.items():
                new_data.extend(
                    {
                        "date": d.get("Date"),
                        "port_code": code,
                        "port_name": code_to_city_map[code],
                        "country": code_to_country_map[code],
                        "measure": k,
                        "value": d.get(code),
                    }
                    for d in v
                    if d.get(code)
                )
            df = (
                DataFrame(new_data)
                .sort_values(by=["date", "measure"])
                .reset_index(drop=True)
                if df.empty
                else concat(
                    [
                        df,
                        DataFrame(new_data)
                        .sort_values(by=["date", "measure"])
                        .reset_index(drop=True),
                    ]
                )
            )

        df = df.pivot_table(
            index=["date", "port_code", "port_name", "country"],
            columns="measure",
            values="value",
            sort=False,
            observed=True,
        )
        cols_map = {
            "Dwelling times imports": "import_dwell_time",
            "Dwelling times exports": "export_dwell_time",
            "Imports": "import_teu",
            "Exports": "export_teu",
        }
        df = df.rename(columns=cols_map).reset_index().convert_dtypes()
        df.country = df.country.map(
            {v: k.replace("_", " ").title() for k, v in COUNTRY_MAP.items()}
        )
        df.date = to_datetime(df.date).dt.date

        if query.start_date:
            df = df[df.date >= query.start_date]

        if query.end_date:
            df = df[df.date <= query.end_date]

        if len(df) == 0:
            raise EmptyDataError(
                f"No data found for the provided dates. Data has a range from {df.date.min()} to {df.date.max()}."
            )

        return [
            EconDbPortVolumeData.model_validate(d) for d in df.to_dict(orient="records")
        ]