async def aextract_data(
        query: OECDGdpForecastQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the OECD endpoint."""
        # pylint: disable=import-outside-toplevel
        from io import StringIO  # noqa
        from openbb_oecd.utils.helpers import oecd_date_to_python_date
        from pandas import read_csv
        from openbb_core.provider.utils.helpers import amake_request

        freq = "Q" if query.frequency == "quarter" else "A"

        measure_dict = {
            "current_prices": "GDP_USD",  # This gives questionable results.
            "volume": "GDPV_USD",
            "capita": "GDPVD_CAP",
            "growth": "GDPV_ANNPCT",
            "deflator": "PGDP",
        }
        measure = measure_dict[query.units]  # type: ignore

        if query.units == "capita" and freq == "Q":
            warn(
                "Capita data is not available for quarterly data, using annual data instead."
            )
            freq = "A"

        def country_string(input_str: str):
            """Convert the list of countries to an abbreviated string."""
            if input_str == "all":
                return ""
            _countries = input_str.split(",")

            return "+".join(
                [
                    COUNTRY_TO_CODE_GDP_FORECAST[country.lower()]
                    for country in _countries
                ]
            )

        country = country_string(query.country)

        url = (
            "https://sdmx.oecd.org/public/rest/data/OECD.ECO.MAD,DSD_EO@DF_EO,1.1"
            + f"/{country}.{measure}.{freq}?"
            + f"startPeriod={query.start_date}&endPeriod={query.end_date}"
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
                CODE_TO_COUNTRY_GDP_FORECAST.get(d, d)
                .replace("_", " ")
                .replace("asia", "Dynamic Asian Economies")
                .title()
            )
            for d in df.country
        ]
        df.date = df.date.apply(oecd_date_to_python_date)
        df = df[df["value"].notnull()]

        if query.units != "growth":
            df["value"] = df.value.astype("int64")
            df = df[df["value"] > 0]

        if query.units == "growth":
            df["value"] = df.value.astype("float64") / 100

        df = df[df["value"] > 0]
        df = df.sort_values(by=["date", "value"], ascending=[True, False])

        return df.to_dict(orient="records")