async def aextract_data(
        query: DeribitOptionsChainsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Extract the data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import json
        import websockets
        from openbb_deribit.utils.helpers import get_options_symbols
        from pandas import to_datetime
        from websockets.asyncio.client import connect
        from warnings import warn

        # We need to identify each option contract in order to fetch the chains data.
        symbols_dict: dict[str, str] = {}

        try:
            symbols_dict = await get_options_symbols(query.symbol)  # type: ignore
        except OpenBBError as e:
            raise OpenBBError(e) from e

        # For each expiration, we need to create a websocket connection to fetch the data.
        # We subscribe to each contract symbol and break the connection when we have all the data for an expiry.
        # If it takes too long, we break the connection and return an error message.
        results: list = []
        messages: set = set()

        async def call_api(expiration):
            """Call the Deribit API."""
            symbols = symbols_dict[expiration]
            received_symbols: set = set()
            msg = {
                "jsonrpc": "2.0",
                "id": 3600,
                "method": "public/subscribe",
                "params": {"channels": ["ticker." + d + ".100ms" for d in symbols]},
            }
            async with connect("wss://www.deribit.com/ws/api/v2") as websocket:
                await websocket.send(json.dumps(msg))
                try:
                    await asyncio.wait_for(
                        receive_data(websocket, symbols, received_symbols), timeout=2.0
                    )
                except asyncio.TimeoutError:
                    messages.add(f"Timeout reached for {expiration}, data incomplete.")

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

        tasks = [
            asyncio.create_task(call_api(expiration)) for expiration in symbols_dict
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        if messages and not results:
            raise OpenBBError(", ".join(messages))

        if results and messages:
            for message in messages:
                warn(message)

        if not results and not messages:
            raise EmptyDataError("All requests returned empty with no error messages.")

        return results