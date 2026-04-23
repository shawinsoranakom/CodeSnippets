async def get_one(url, series):
            """Get data for one series."""
            res = await amake_request(url, response_callback=response_callback)
            if res:
                df = read_html(StringIO(res))[0]  # type: ignore
                if not df.empty:
                    df["Date"] = to_datetime(df["Date"]).dt.date
                    df = df.sort_values("Date").reset_index(drop=True)
                    if query.start_date:
                        df = df[df["Date"] >= query.start_date]
                    if query.end_date:
                        df = df[df["Date"] <= query.end_date]
                    df["Value"] = df["Value"].apply(
                        lambda x: (
                            x.strip().replace("† ", "").replace("%", "")
                            if isinstance(x, str)
                            else x
                        )
                    )
                    df["name"] = series
                    if "growth" in series or "yield" in series:
                        df["Value"] = df["Value"].astype(float) / 100

                    results.extend(df.replace({nan: None}).to_dict(orient="records"))
            else:
                warn(f"Failed to get data for {series}.")