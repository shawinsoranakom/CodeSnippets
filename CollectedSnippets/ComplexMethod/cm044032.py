async def aextract_data(
        query: OECDGdpNominalQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the OECD endpoint."""
        # pylint: disable=import-outside-toplevel
        from io import StringIO  # noqa
        from openbb_oecd.utils.helpers import oecd_date_to_python_date
        from numpy import nan
        from pandas import read_csv
        from openbb_core.provider.utils.helpers import amake_request

        if query.units == "index":
            unit = "INDICES"
        elif query.units == "capita":
            unit = "CAPITA"
        else:
            unit = "USD"

        frequency = "Q" if query.frequency == "quarter" else "A"
        price_base = "V" if query.price_base == "current_prices" else "LR"

        if unit == "INDICES" and price_base == "V":
            price_base = "DR"

        def country_string(input_str: str):
            """Convert the list of countries to an abbreviated string."""
            if input_str == "all":
                return ""
            _countries = input_str.split(",")

            return "+".join([COUNTRY_TO_CODE_GDP[country] for country in _countries])

        country = country_string(query.country) if query.country else ""

        url = (
            f"https://sdmx.oecd.org/public/rest/data/OECD.SDD.NAD,DSD_NAMAIN1@DF_QNA_EXPENDITURE_{unit},1.1"
            + f"/{frequency}..{country}.S1..B1GQ.....{price_base}..?"
            + f"&startPeriod={query.start_date}&endPeriod={query.end_date}"
            + "&dimensionAtObservation=TIME_PERIOD&detail=dataonly&format=csvfile"
        )
        if query.units == "capita":
            url = url.replace("B1GQ", "B1GQ_POP")

        async def response_callback(response, _):
            """Response callback."""
            if response.status != 200:
                raise OpenBBError(f"Error with the OECD request: {response.status}")
            return await response.text()

        response = await amake_request(
            url, timeout=30, response_callback=response_callback
        )

        df = read_csv(StringIO(response)).get(["REF_AREA", "TIME_PERIOD", "OBS_VALUE"])  # type: ignore
        if df.empty:  # type: ignore
            raise EmptyDataError()
        df = df.rename(columns={"REF_AREA": "country", "TIME_PERIOD": "date", "OBS_VALUE": "value"})  # type: ignore

        def apply_map(x):
            """Apply the country map."""
            v = CODE_TO_COUNTRY_GDP.get(x, x)
            v = v.replace("_", " ").title()
            return v

        df["country"] = df["country"].apply(apply_map).str.replace("Oecd", "OECD")
        df["date"] = df["date"].apply(oecd_date_to_python_date)
        df = df[(df["date"] <= query.end_date) & (df["date"] >= query.start_date)]
        if query.units == "level":
            df["value"] = (df["value"].astype(float) * 1_000_000).astype("int64")

        df = df.sort_values(by=["date", "value"], ascending=[True, False])

        return df.replace({nan: None}).to_dict(orient="records")