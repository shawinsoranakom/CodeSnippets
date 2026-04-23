async def aextract_data(
        query: ImfPortVolumeQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract data from the IMF Port Volume API."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_imf.utils.port_watch_helpers import get_daily_port_activity_data

        port_codes = (
            get_port_ids_by_country(query.country)
            if query.country
            else (
                query.port_code.split(",")
                if isinstance(query.port_code, str)
                else query.port_code
            )
        )

        if not port_codes:
            raise OpenBBError("Expected values as valid portIDs, got None instead.")

        output: list = []

        async def fetch_port_data(port_code: str):
            """Fetch data for a single port."""
            try:
                data = await get_daily_port_activity_data(
                    port_code, query.start_date, query.end_date
                )
                if data:
                    output.extend(data)
            except Exception as e:
                raise OpenBBError(
                    f"Failed to fetch data for port {port_code}: {e} -> {e.args}"
                ) from e

        tasks = [fetch_port_data(port_code=port_code) for port_code in port_codes]

        tasks_results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in tasks_results:
            if isinstance(result, Exception):
                raise OpenBBError(
                    f"Error fetching port data: {result} -> {result.args[0]}"
                )

        if not output:
            raise OpenBBError(
                f"No data found for the specified port(s). {port_codes}"
                " Ensure the port_code is correct and available in the IMF PortWatch dataset."
            )
        return output