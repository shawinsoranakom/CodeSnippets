def extract_data(
        query: OECDHousePriceIndexQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the OECD endpoint."""
        # pylint: disable=import-outside-toplevel
        from io import StringIO  # noqa
        from openbb_oecd.utils.helpers import oecd_date_to_python_date  # noqa
        from openbb_core.provider.utils.helpers import make_request  # noqa
        from pandas import read_csv  # noqa

        frequency = frequency_dict.get(query.frequency, "Q")
        transform = transform_dict.get(query.transform, "PA")

        def country_string(input_str: str):
            if input_str == "all":
                return ""
            _countries = input_str.split(",")
            return "+".join([COUNTRY_TO_CODE_RGDP[country] for country in _countries])

        country = country_string(query.country) if query.country else ""
        start_date = query.start_date.strftime("%Y-%m") if query.start_date else ""
        end_date = query.end_date.strftime("%Y-%m") if query.end_date else ""
        url = (
            "https://sdmx.oecd.org/public/rest/data/OECD.SDD.TPS,DSD_RHPI_TARGET@DF_RHPI_TARGET,1.0/"
            + f"COU.{country}.{frequency}.RHPI.{transform}....?"
            + f"startPeriod={start_date}&endPeriod={end_date}"
            + "&dimensionAtObservation=TIME_PERIOD&detail=dataonly"
        )
        headers = {"Accept": "application/vnd.sdmx.data+csv; charset=utf-8"}
        response = make_request(url, headers=headers, timeout=20)
        if response.status_code == 404 and frequency == "M":
            warn("No monthly data found. Switching to quarterly data.")
            response = make_request(
                url.replace(".M.RHPI.", ".Q.RHPI."), headers=headers
            )
        if response.status_code != 200:
            raise OpenBBError(
                f"Error with the OECD request (HTTP {response.status_code}): `{response.text}`"
            )
        df = read_csv(StringIO(response.text)).get(
            ["REF_AREA", "TIME_PERIOD", "OBS_VALUE"]
        )
        if df.empty:
            raise EmptyDataError()
        df = df.rename(
            columns={"REF_AREA": "country", "TIME_PERIOD": "date", "OBS_VALUE": "value"}
        )
        df.country = df.country.map(CODE_TO_COUNTRY_RGDP)
        df.date = df.date.apply(oecd_date_to_python_date)
        df = (
            df.query("value.notnull()")
            .set_index(["date", "country"])
            .sort_index()
            .reset_index()
        )

        return df.to_dict("records")