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