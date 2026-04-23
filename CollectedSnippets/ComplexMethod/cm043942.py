async def get_daily_port_activity_data(
    port_id, start_date: str | None = None, end_date: str | None = None
) -> list:
    """Get the daily port activity data for a specific port ID.

    Parameters
    ----------
    port_id : str
        The port ID for which to fetch daily activity data.

    Returns
    -------
    list
        A list of dictionaries, each representing daily activity data for the specified port.
    """
    # pylint: disable=import-outside-toplevel
    from datetime import datetime  # noqa
    from openbb_core.app.model.abstract.error import OpenBBError
    from openbb_core.provider.utils.helpers import get_async_requests_session

    if port_id is None:
        raise OpenBBError(
            ValueError("Either port_id or country_code must be provided.")
        )

    if start_date is not None and end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if start_date is None and end_date is not None:
        start_date = "2019-01-01"

    def get_port_url(offset: int):
        """Construct the URL for fetching chokepoint data with offset."""
        nonlocal port_id, start_date, end_date
        return (
            (
                DAILY_TRADE_BASE_URL
                + f"where=portid%20%3D%20%27{port_id.upper()}%27&"  # type: ignore
                + f"outFields=*&orderByFields=date&returnZ=true&resultOffset={offset}&resultRecordCount=1000"
                + "&maxRecordCountFactor=5&outSR=&f=json"
            )
            if start_date is None and end_date is None
            else (
                DAILY_TRADE_BASE_URL
                + f"where=portid%20%3D%20%27{port_id.upper()}%27%20"
                + f"AND%20date%20>%3D%20TIMESTAMP%20%27{start_date}%2000%3A00%3A00%27"
                + f"%20AND%20date%20<%3D%20TIMESTAMP%20%27{end_date}%2000%3A00%3A00%27&"
                + f"outFields=*&orderByFields=date&returnZ=true&resultOffset={offset}&resultRecordCount=1000"
                + "&maxRecordCountFactor=5&outSR=&f=json"
            )
        )

    offset: int = 0
    output: dict = {}
    url = get_port_url(offset)

    async with await get_async_requests_session() as session:
        async with await session.get(url) as response:
            data = {}

            if response.status != 200:
                raise OpenBBError(f"Failed to fetch data: {response.status}")
            data = await response.json()

        if "features" in data:
            output = data.copy()

        while data.get("exceededTransferLimit") is True:
            offset += len(data["features"])
            url = get_port_url(offset)

            async with await session.get(url) as response:
                data = {}
                if response.status != 200:
                    raise OpenBBError(f"Failed to fetch data: {response.status}")
                data = await response.json()

            if "features" in data:
                output["features"].extend(data["features"])

        final_output: list = []

        for feature in output["features"]:
            date = datetime(
                feature["attributes"]["year"],
                feature["attributes"]["month"],
                feature["attributes"]["day"],
            ).strftime("%Y-%m-%d")
            final_output.append(
                {
                    "date": date,
                    **{
                        k: v
                        for k, v in feature["attributes"].items()
                        if k not in ["year", "month", "day", "date", "ObjectId"]
                    },
                }
            )

    return final_output