async def get_one_country(c):
            """Get data for one country."""
            c = c.upper() if len(c) == 2 else c.lower()
            if len(c) != 2:
                c = COUNTRY_MAP.get(c, c)
                if len(c) != 2 or c.upper() not in MAP_COUNTRY:
                    messages.append(f"Invalid country code -> {c}")
                    return

            URL = f"https://www.econdb.com/widgets/top-trade-items/data/?country={c.upper()}&split_by=country"
            result: list = []
            row: dict = {}
            try:
                res = await amake_request(URL)
            except ContentTypeError as e:
                if len(countries) == 1:
                    raise OpenBBError(e) from e
                messages.append(f"No data available for the country -> {c}")
                return

            plots = res.get("plots", [])  # type: ignore
            data = plots[0].pop("data", []) if plots else []
            meta = plots[0] if plots else {}

            if not data or (len(data) == 1 and data[0].get("Value million USD") == 0):
                messages.append(f"No data available for the country -> {c}")
                return

            origin_country = MAP_COUNTRY.get(c, c)

            for item in data:
                row = {
                    "origin_country": origin_country.replace("_", " ").title(),
                    **item,
                    "units": (
                        meta.get("series", [])[0]
                        .get("code", "")
                        .replace("Value million", "Millions of")
                        if meta.get("series", [])
                        else ""
                    ),
                    "title": meta.get("title", ""),
                    "footnote": meta.get("footnote", ""),
                }
                result.append(
                    {
                        (
                            "value"
                            if k == "Value million USD"
                            else "destination_country" if k == "Country" else k
                        ): (
                            MAP_COUNTRY.get(v, v).replace("_", " ").title()
                            if k == "Country"
                            else v
                        )
                        for k, v in row.items()
                        if v and v != 0
                    }
                )
            if result:
                results.extend(result)
            else:
                messages.append(f"No data returned for the country -> {c}")