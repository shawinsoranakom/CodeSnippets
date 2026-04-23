async def get_one(url, underlying_price):
            """Get the chain for a single expiration."""
            chain = await amake_request(url, headers=HEADERS)
            if chain.get("options") and isinstance(chain["options"].get("option", []), list):  # type: ignore
                data = chain["options"]["option"]  # type: ignore
                for d in data.copy():
                    # Remove any strikes returned without data.
                    keys = ["last", "bid", "ask"]
                    if all(d.get(key) in [0, "0", None] for key in keys):
                        data.remove(d)
                        continue
                    # Flatten the nested greeks dictionary
                    greeks = d.pop("greeks")
                    if greeks is not None:
                        d.update(**greeks)
                    # Pop fields that are duplicate information or not of interest.
                    to_pop = [
                        "root_symbol",
                        "exch",
                        "type",
                        "expiration_type",
                        "description",
                        "average_volume",
                    ]
                    _ = [d.pop(key) for key in to_pop if key in d]
                    # Add the DTE field to the data for easier filtering later.
                    d["dte"] = (
                        datetime.strptime(d["expiration_date"], "%Y-%m-%d").date()
                        - datetime.now().date()
                    ).days
                    if underlying_price is not None:
                        d["underlying_price"] = underlying_price

                results.extend(data)