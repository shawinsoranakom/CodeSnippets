async def aextract_data(
        query: FredHighQualityMarketCorporateBondQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from dateutil import parser  # noqa
        from openbb_core.provider.utils.helpers import amake_request  # noqa

        api_key = credentials.get("fred_api_key") if credentials else ""

        element_id = "219299" if query.yield_curve == "spot" else "219294"
        dates: list = [""]
        if query.date:
            if query.date and isinstance(query.date, dateType):
                query.date = query.date.strftime("%Y-%m-%d")
            dates = query.date.split(",")  # type: ignore
            dates = [d.replace(d[-2:], "01") if len(d) == 10 else d for d in dates]
            dates = list(set(dates))
            dates = [f"&observation_date={date}" for date in dates if date] if dates else ""  # type: ignore
        URLS = [
            f"https://api.stlouisfed.org/fred/release/tables?release_id=402&element_id={element_id}"
            + f"{date}&include_observation_values=true&api_key={api_key}"
            + "&file_type=json"
            for date in dates
        ]
        results = []

        async def get_one(URL):
            """Get the observations for a single date."""
            data = await amake_request(URL)
            if data:
                elements = dict(data.get("elements", {}).items())  # type: ignore
                for k, v in elements.items():  # pylint: disable=W0612
                    value = v.get("observation_value")
                    if not value:
                        continue
                    maturity = v.get("name").lower().split("-")
                    results.append(
                        {
                            "date": parser.parse(
                                v.get("observation_date"),
                            ).date(),
                            "rate": float(value) / 100,
                            "maturity": (maturity[1] + "_" + maturity[0]).replace(
                                " ", ""
                            ),
                        }
                    )

        await asyncio.gather(*[get_one(URL) for URL in URLS])

        return results