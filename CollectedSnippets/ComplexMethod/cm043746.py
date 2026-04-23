async def get_one(ticker):
        """Get data for one symbol."""
        ticker = ticker.upper()
        message = f"Symbol Error: No data was found for, {ticker} and {fact}"
        cik = await symbol_map(ticker)
        if cik == "":
            message = f"Symbol Error: No CIK was found for, {ticker}"
            warn(message)
            messages.append(message)
        else:
            url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{cik}/{taxonomy}/{fact}.json"
            response: dict | list[dict] = {}
            try:
                response = await fetch_data(url, use_cache, False)
            except Exception as _:  # pylint: disable=W0718
                warn(message)
                messages.append(message)
            if response:
                units = response.get("units", {})  # type: ignore
                metadata[ticker] = {
                    "cik": response.get("cik", ""),  # type: ignore
                    "taxonomy": response.get("taxonomy", ""),  # type: ignore
                    "tag": response.get("tag", ""),  # type: ignore
                    "label": response.get("label", ""),  # type: ignore
                    "description": response.get("description", ""),  # type: ignore
                    "name": response.get("entityName", ""),  # type: ignore
                    "units": (
                        list(units) if units and len(units) > 1 else list(units)[0]
                    ),
                }
                for k, v in units.items():
                    unit = k
                    values = v
                    for item in values:
                        item["unit"] = unit
                        item["symbol"] = ticker
                        item["cik"] = metadata[ticker]["cik"]
                        item["name"] = metadata[ticker]["name"]
                        item["fact"] = metadata[ticker]["label"]
                    results.extend(values)