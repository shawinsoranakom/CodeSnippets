async def aextract_data(
        query: NasdaqEconomicCalendarQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Nasdaq endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_core.provider.utils.helpers import amake_request
        from openbb_nasdaq.utils.helpers import get_headers, date_range

        IPO_HEADERS = get_headers(accept_type="json")
        data: list[dict] = []
        dates = [
            date.strftime("%Y-%m-%d")
            for date in date_range(query.start_date, query.end_date)
            if date.weekday() < 5  # Exclude weekends
        ]

        async def get_calendar_data(date: str):
            """Get the calendar data for a single date."""
            response: list = []
            url = f"https://api.nasdaq.com/api/calendar/economicevents?date={date}"
            r_json = await amake_request(url=url, headers=IPO_HEADERS)

            if (
                isinstance(r_json, dict)
                and (status := r_json.get("status", {}))
                and (messages := status.get("bCodeMessage", []))
                and (error_message := messages[0].get("errorMessage", ""))
                and not data
            ):
                raise OpenBBError(
                    f"Nasdaq Error -> {error_message}",
                )

            if r_json is not None and r_json.get("data"):  # type: ignore
                response = r_json["data"].get("rows")  # type: ignore

            if response:
                response = [
                    {
                        **{k: v for k, v in item.items() if k != "gmt"},
                        "date": (
                            f"{date} 00:00"
                            if item.get("gmt") == "All Day"
                            else f"{date} {item.get('gmt', '')}".replace(
                                "Tentative", "00:00"
                            ).replace("24H", "00:00")
                        ),
                    }
                    for item in response
                ]
                data.extend(response)

        await asyncio.gather(*[get_calendar_data(date) for date in dates])

        if not data:
            raise OpenBBError(
                "There was an error with the request and it was returned empty."
            )

        if query.country:
            country = (
                query.country.split(",") if "," in query.country else query.country
            )
            country = [country] if isinstance(country, str) else country

            return [
                d
                for d in data
                if d.get("country", "").lower().replace(" ", "_") in country
            ]

        return data