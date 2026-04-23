def extract_data(
        query: OECDCPIQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the OECD endpoint."""
        # pylint: disable=import-outside-toplevel
        from requests.exceptions import HTTPError  # noqa
        from openbb_oecd.utils import helpers  # noqa

        methodology = "HICP" if query.harmonized is True else "N"
        unit = "mom" if query.transform == "period" else query.transform
        query.frequency = (
            "monthly"
            if query.harmonized is True and query.frequency == "quarter"
            else query.frequency
        )
        frequency = query.frequency[0].upper()
        units = {
            "index": "IX",
            "yoy": "PA",
            "mom": "PC",
        }[unit]
        expenditure = (
            "" if query.expenditure == "all" else expenditure_dict[query.expenditure]
        )

        def country_string(input_str: str):
            if input_str == "all":
                return ""
            _countries = input_str.split(",")
            return "+".join([COUNTRY_TO_CODE_CPI[country] for country in _countries])

        country = country_string(query.country)
        # For caching, include this in the key
        query_dict = {
            k: v
            for k, v in query.__dict__.items()
            if k not in ["start_date", "end_date"]
        }

        url = (
            f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_PRICES@DF_PRICES_ALL,1.0/"
            f"{country}.{frequency}.{methodology}.CPI.{units}.{expenditure}.N."
        )
        try:
            data = helpers.get_possibly_cached_data(
                url, function="economy_cpi", query_dict=query_dict
            )
        except HTTPError as exc:
            raise OpenBBError("No data found for the given query.") from exc
        url_query = f"METHODOLOGY=='{methodology}' & UNIT_MEASURE=='{units}' & FREQ=='{frequency}'"

        if country != "all":
            if "+" in country:
                _countries = country.split("+")
                country_conditions = " or ".join(
                    [f"REF_AREA=='{c}'" for c in _countries]
                )
                url_query += f" & ({country_conditions})"
            else:
                url_query = url_query + f" & REF_AREA=='{country}'"
        url_query = (
            url_query + f" & EXPENDITURE=='{expenditure}'"
            if query.expenditure != "all"
            else url_query
        )
        # Filter down
        data = (
            data.query(url_query)
            .reset_index(drop=True)[["REF_AREA", "TIME_PERIOD", "VALUE", "EXPENDITURE"]]
            .rename(
                columns={
                    "REF_AREA": "country",
                    "TIME_PERIOD": "date",
                    "VALUE": "value",
                    "EXPENDITURE": "expenditure",
                }
            )
        )
        data["country"] = data["country"].map(CODE_TO_COUNTRY_CPI)
        data["expenditure"] = data["expenditure"].map(expenditure_dict_rev)
        data["date"] = data["date"].apply(helpers.oecd_date_to_python_date)
        data = data[
            (data["date"] <= query.end_date) & (data["date"] >= query.start_date)
        ]
        # Normalize the percent value.
        if query.transform in ("yoy", "period"):
            data["value"] = data["value"].astype(float) / 100

        return data.fillna("N/A").replace("N/A", None).to_dict(orient="records")