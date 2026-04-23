async def aextract_data(
        query: IntrinioOptionsSnapshotsQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> "DataFrame":
        """Return the raw data from the Intrinio endpoint."""
        # pylint: disable=import-outside-toplevel
        import gzip  # noqa
        from io import BytesIO  # noqa
        from openbb_core.provider.utils.helpers import amake_request  # noqa
        from pandas import DataFrame, read_csv  # noqa

        api_key = credentials.get("intrinio_api_key") if credentials else ""

        # This gets the URL to the actual file.
        url = f"https://api-v2.intrinio.com/options/snapshots?api_key={api_key}"
        if query.date:
            url += f"&at_datetime={query.date}"

        try:
            response = await amake_request(url, **kwargs)
        except Exception as exc:
            raise OpenBBError("Could not fetch data from Intrinio.") from exc

        if isinstance(response, dict) and "error" in response:
            raise OpenBBError(
                f"{response.get('error')}. Message: {response.get('message')}"
            )
        urls = []
        # Get the URL to the CSV file.
        if response.get("snapshots"):  # type: ignore
            for d in response["snapshots"]:  # type: ignore
                if d.get("files"):
                    for f in d["files"]:
                        if f.get("url"):
                            urls.append(f.get("url"))
        if not urls:
            raise OpenBBError("No snapshots found.")

        async def response_callback(response, _):
            """Response Callback."""
            return await response.read()

        async def get_csv(url) -> DataFrame:
            """Return the CSV data."""
            try:
                response = await amake_request(
                    url, response_callback=response_callback, **kwargs
                )
                df = DataFrame()
                if isinstance(response, bytes):
                    file = gzip.decompress(response)
                    df = read_csv(BytesIO(file))

                return df

            except Exception as exc:
                try:
                    df = read_csv(response)
                    return df
                except Exception:
                    raise OpenBBError("Could not read file from URL.") from exc

        # There should only be one URL with this bulk data.
        return await get_csv(urls[0])