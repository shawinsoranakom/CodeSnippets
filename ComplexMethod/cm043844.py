async def receive_data(websocket, symbols, received_symbols):
            """Receive the data from the websocket with a timeout."""
            while True:
                try:
                    response = await websocket.recv()
                except websockets.ConnectionClosed:
                    break
                data = json.loads(response)

                if "params" not in data:
                    continue

                if "error" in data and data.get("error"):
                    messages.add(f"Error while receiving data -> {data['error']}")
                    break

                res = data.get("params", {}).get("data", {})
                symbol = res.get("instrument_name")

                # While we are handling the data, we will parse the message.
                if symbol not in received_symbols:
                    received_symbols.add(symbol)
                    stats = res.pop("stats", {})
                    greeks = res.pop("greeks", {})
                    timestamp = res.pop("timestamp", None)
                    underlying_symbol = res.get("underlying_index")

                    if underlying_symbol == "index_price":
                        res["underlying_index"] = symbol.split("-")[0].replace("_", "-")

                    res["timestamp"] = to_datetime(
                        timestamp, unit="ms", utc=True
                    ).tz_convert("America/New_York")

                    if res.get("estimated_delivery_price") == res.get("index_price"):
                        _ = res.pop("estimated_delivery_price", None)

                    _ = res.pop("state", None)
                    result = {
                        "expiration": to_datetime(symbol.split("-")[1]).date(),
                        "strike": (
                            float(symbol.split("-")[2].replace("d", "."))
                            if "d" in symbol.split("-")[2]
                            else int(symbol.split("-")[2])
                        ),
                        "option_type": (
                            "call"
                            if symbol.endswith("-C")
                            else "put" if symbol.endswith("-P") else None
                        ),
                        **res,
                        **stats,
                        **greeks,
                    }
                    result["dte"] = (
                        result["expiration"] - to_datetime("today").date()
                    ).days
                    results.append(result)

                    if len(received_symbols) == len(symbols):
                        await websocket.close()
                        break