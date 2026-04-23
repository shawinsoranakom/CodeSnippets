async def aextract_data(
        query: IntrinioMarketSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list[dict]:
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        import gzip  # noqa
        from datetime import timezone as datetime_timezone  # noqa
        from io import BytesIO  # noqa
        from openbb_core.provider.utils.helpers import (
            amake_request,
            safe_fromtimestamp,
        )  # noqa
        from pandas import DataFrame, notna, read_csv, to_datetime  # noqa

        api_key = credentials.get("intrinio_api_key") if credentials else ""

        # This gets the URL to the actual file.
        url = f"https://api-v2.intrinio.com/securities/snapshots?api_key={api_key}"
        if query.date:
            url += f"&at_datetime={query.date}"

        response = await amake_request(url, **kwargs)

        if isinstance(response, dict) and "error" in response:
            raise OpenBBError(
                f"Error: {response.get('error')}. Message: {response.get('message')}"
            )
        urls: list = []
        # Get the URL to the CSV file.
        if response.get("snapshots"):  # type: ignore
            for d in response["snapshots"]:  # type: ignore
                if d.get("files"):
                    for f in d["files"]:
                        if f.get("url"):
                            urls.append(f.get("url"))
        if not urls:
            raise OpenBBError("No snapshots found.")

        results: list = []

        async def response_callback(response, _):
            """Response Callback."""
            return await response.read()

        async def get_csv(url):
            """Return the CSV data."""
            response = await amake_request(
                url, response_callback=response_callback, **kwargs
            )
            df = DataFrame()
            if isinstance(response, bytes):
                file = gzip.decompress(response)
                df = read_csv(BytesIO(file))
            if df.empty:
                raise OpenBBError("Empty CSV file.")
            df.columns = df.columns.str.lower().str.replace(" ", "_")

            df = (
                df.dropna(how="all", axis=1)
                .dropna(subset=["trade_price", "last_trade_timestamp", "symbol"])
                .sort_values("last_trade_timestamp", ascending=False)
            )[
                [
                    "symbol",
                    "trade_price",
                    "trade_size",
                    "total_trade_volume",
                    "bid_size",
                    "bid_price",
                    "ask_price",
                    "ask_size",
                    "last_trade_timestamp",
                    "last_bid_timestamp",
                    "last_ask_timestamp",
                ]
            ]

            for col in [
                "last_trade_timestamp",
                "last_bid_timestamp",
                "last_ask_timestamp",
            ]:
                df[col] = (
                    to_datetime(
                        df[col].apply(
                            lambda x: (
                                safe_fromtimestamp(x, tz=datetime_timezone.utc)
                                if notna(x)
                                else x
                            )
                        )
                    )
                    .dt.tz_convert("America/New_York")
                    .dt.floor("s")
                )

            for c in ["trade_size", "total_trade_volume"]:
                df[c] = df[c].astype("int64")

            # Clear out NaN and non-numeric values with None.
            df = (
                df.replace("Max", None)
                .replace("Min", None)
                .replace(0, None)
                .fillna("N/A")
                .replace("N/A", None)
            )

            if len(df) > 0:
                results.extend(df.reset_index(drop=True).to_dict(orient="records"))

        await asyncio.gather(*[get_csv(url) for url in urls])

        return results