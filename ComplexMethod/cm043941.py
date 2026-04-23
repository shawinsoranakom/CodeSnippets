async def get_daily_chokepoint_data(
    chokepoint_id, start_date: str | None = None, end_date: str | None = None
) -> list:
    """Get the daily chokepoint data for a specific chokepoint and date range.

    Parameters
    ----------
    chokepoint_id : str
        The ID of the chokepoint (e.g., "chokepoint1"). 1-24 are valid IDs
    """
    # pylint: disable=import-outside-toplevel
    from datetime import datetime  # noqa
    from openbb_core.app.model.abstract.error import OpenBBError
    from openbb_core.provider.utils.helpers import get_async_requests_session

    if start_date is not None and end_date is None:
        end_date = datetime.now().strftime("%Y-%m-%d")

    if start_date is None and end_date is not None:
        start_date = "2019-01-01"

    def get_chokepoints_url(offset: int):
        """Construct the URL for fetching chokepoint data with offset."""
        nonlocal chokepoint_id
        return (
            (
                CHOKEPOINTS_BASE_URL
                + f"where=portid%20%3D%20%27{chokepoint_id.upper()}%27"
                + f"AND%20date%20>%3D%20TIMESTAMP%20%27{start_date}%2000%3A00%3A00%27"
                + f"%20AND%20date%20<%3D%20TIMESTAMP%20%27{end_date}%2000%3A00%3A00%27&"
                + f"outFields=*&orderByFields=date&returnZ=true&resultOffset={offset}&resultRecordCount=1000"
                + "&maxRecordCountFactor=5&outSR=&f=json"
            )
            if start_date is not None and end_date is not None
            else (
                CHOKEPOINTS_BASE_URL
                + f"where=portid%20%3D%20%27{chokepoint_id.upper()}%27&"
                + f"outFields=*&orderByFields=date&returnZ=true&resultOffset={offset}&resultRecordCount=1000"
                + "&maxRecordCountFactor=5&outSR=&f=json"
            )
        )

    offset: int = 0
    output: dict = {}
    url = get_chokepoints_url(offset)

    async with await get_async_requests_session() as session:
        async with await session.get(url) as response:
            data: dict = {}

            if response.status != 200:
                raise OpenBBError(f"Failed to fetch data: {response.status}")
            data = await response.json()

        if "features" in data:
            output = data.copy()

        while data.get("exceededTransferLimit") is True:
            offset += len(data["features"])
            url = get_chokepoints_url(offset)

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