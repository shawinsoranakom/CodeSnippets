async def get_one(symbol, intraday: bool = False):
            """Get data for one symbol."""
            if intraday is True:
                adjusted = query.adjustment != "unadjusted"
                if query.adjustment == "splits_only":
                    warn(
                        "Intraday does not support 'splits_only'. Using 'splits_and_dividends' instead."
                    )
                url = (
                    f"https://www.alphavantage.co/query?{query_str.replace('_ADJUSTED', '')}"
                    f"&symbol={symbol}&adjusted={str(adjusted).lower()}"
                )
                dates = (
                    date_range(start=query.start_date, end=query.end_date)
                    .strftime("%Y-%m")
                    .unique()
                    .tolist()
                )
                urls = [f"{url}&month={date}&apikey={api_key}" for date in dates]
                return await amake_requests(urls, response_callback=intraday_callback)

            # We will resample the intervals ourselves to get the correct data.
            url = (
                f"https://www.alphavantage.co/query?{query_str.replace('MONTHLY', 'DAILY').replace('WEEKLY', 'DAILY')}"
                f"&symbol={symbol}&apikey={api_key}"
            )
            result = await amake_request(url, response_callback=callback)
            if not result:
                warn(f"Symbol Error: No data found for {symbol}")
            if result:
                data = read_csv(BytesIO(result))  # type: ignore
                if len(data) > 0:
                    data.rename(
                        columns={
                            "timestamp": "date",
                            "dividend_amount": "dividend",
                            "adjusted close": "adj_close",
                            "dividend amount": "dividend",
                            "adjusted_close": "adj_close",
                            "split_coefficient": "split_factor",
                        },
                        inplace=True,
                    )
                    if "date" in data.columns:
                        data["date"] = data["date"].apply(to_datetime)
                        data.set_index("date", inplace=True)
                        # The returned data when 'adjusted=true' from the API does not return a usable OHLCV data set.
                        # We need to calculate the adjusted prices manually.
                        if query.adjustment != "unadjusted":
                            temp = data.copy()
                            temp["dividend_factor"] = (
                                temp["close"] - temp["dividend"]
                            ) / temp["close"]
                            temp["volume_factor"] = temp["split_factor"]
                            temp["split_factor"] = 1 / temp["split_factor"]
                            adj_cols = ["open", "high", "low", "close", "volume"]
                            divs = query.adjustment == "splits_and_dividends"
                            for col in adj_cols:
                                divs = False if col == "volume" else divs
                                if col in temp.columns:
                                    temp = calculate_adjusted_prices(temp, col, divs)
                            temp["adj_dividend"] = (
                                temp["adj_close"] * (1 - temp["dividend_factor"])
                                if query.adjustment == "splits_only"
                                else temp["close"] * (1 - temp["dividend_factor"])
                            )
                            data["open"] = round(temp["adj_open"], 4)
                            data["high"] = round(temp["adj_high"], 4)
                            data["low"] = round(temp["adj_low"], 4)
                            data["close"] = round(temp["adj_close"], 4)
                            data["volume"] = round(temp["adj_volume"]).astype(int)
                            data["dividend"] = round(temp["adj_dividend"], 4)
                            data.drop(columns=["adj_close"], inplace=True)
                        # Resample the daily data for the interval requested.
                        freq = ""
                        agg_dict = {
                            "open": "first",
                            "high": "max",
                            "low": "min",
                            "close": "last",
                            "volume": "sum",
                            "dividend": "sum",
                            "split_factor": "prod",
                        }
                        if query.adjustment == "unadjusted":
                            agg_dict.pop("dividend")
                            agg_dict.pop("split_factor")
                        if query.interval == "1M":
                            freq = "M"
                        if query.interval == "1W":
                            freq = "W-FRI"
                        if freq in ["M", "W-FRI"]:
                            data = data.resample(freq).agg({**agg_dict})
                        if len(query.symbol.split(",")) > 1:
                            data["symbol"] = symbol

                        data = data.reset_index()
                        if intraday is False:
                            data["date"] = data["date"].dt.date

                        results.extend(data.to_dict("records"))

            return results