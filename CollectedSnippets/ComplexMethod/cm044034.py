async def aextract_data(
        query: OECDCompositeLeadingIndicatorQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the OECD endpoint."""
        # pylint: disable=import-outside-toplevel
        from io import StringIO  # noqa
        from openbb_oecd.utils.helpers import oecd_date_to_python_date
        from pandas import read_csv
        from openbb_core.provider.utils.helpers import amake_request

        COUNTRY_MAP = {v: k.replace("_", " ").title() for k, v in COUNTRIES.items()}

        growth_rate = "GY" if query.growth_rate is True else "IX"
        adjustment = "AA" if query.adjustment == "amplitude" else "NOR"

        if growth_rate == "GY":
            adjustment = ""

        def country_string(input_str: str):
            if input_str == "all":
                return ""
            _countries = input_str.split(",")
            return "+".join([COUNTRIES[country.lower()] for country in _countries])

        country = country_string(query.country) if query.country else ""
        url = (
            "https://sdmx.oecd.org/public/rest/data/OECD.SDD.STES,DSD_STES@DF_CLI,4.1"
            + f"/{country}.M.LI...{adjustment}.{growth_rate}..H"
            + f"?startPeriod={query.start_date}&endPeriod={query.end_date}"
            + "&dimensionAtObservation=TIME_PERIOD&detail=dataonly&format=csvfile"
        )

        async def response_callback(response, _):
            """Response callback."""
            if response.status != 200:
                raise OpenBBError(f"Error with the OECD request: {response.status}")
            return await response.text()

        headers = {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}
        response = await amake_request(
            url, timeout=30, headers=headers, response_callback=response_callback
        )

        df = read_csv(StringIO(response)).get(["REF_AREA", "TIME_PERIOD", "OBS_VALUE"])  # type: ignore

        if df.empty:  # type: ignore
            raise EmptyDataError("No data was found.")

        df = df.rename(columns={"REF_AREA": "country", "TIME_PERIOD": "date", "OBS_VALUE": "value"})  # type: ignore
        df.country = [
            (
                COUNTRY_MAP.get(d, d)
                .replace("Asia5", "Major 5 Asian Economies")
                .replace("Europe4", "Major 4 European Economies")
            )
            for d in df.country
        ]
        df.date = df.date.apply(oecd_date_to_python_date)

        if query.growth_rate is True:
            df.value = df.value.astype(float) / 100

        df = (
            df.query("value.notnull()")
            .set_index(["date", "country"])
            .sort_index()
            .reset_index()
        )

        return df.to_dict("records")