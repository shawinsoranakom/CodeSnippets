async def aextract_data(
        query: ImfPortInfoQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract the raw data from the IMF Port Watch API."""
        # pylint: disable=import-outside-toplevel
        from openbb_core.provider.utils.helpers import get_async_requests_session

        all_ports_url = (
            "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/PortWatch_ports_database/FeatureServer/0/query?"
            + "where=1%3D1&outFields=*&returnGeometry=false&outSR=&f=json"
        )
        try:
            output: list = []
            data: dict = {}

            async with await get_async_requests_session() as session:
                async with await session.get(all_ports_url) as response:
                    if response.status != 200:
                        raise OpenBBError(
                            f"Failed to fetch data: {response.status} -> {response.reason}"
                        )

                    data = await response.json()

                if "features" in data:
                    output.extend(data["features"])

                    if "exceededTransferLimit" in data:
                        while data.get("exceededTransferLimit"):
                            offset = len(output)
                            url = f"{all_ports_url}&resultOffset={offset}"

                            async with await session.get(url) as response:
                                if response.status != 200:
                                    raise OpenBBError(
                                        f"Failed to fetch data: {response.status}"
                                    )

                                data = await response.json()
                                if "features" in data:
                                    output.extend(data["features"])

            return sorted(
                output,
                key=lambda x: x["attributes"]["vessel_count_total"],
                reverse=True,
            )

        except Exception as e:
            raise OpenBBError(e) from e