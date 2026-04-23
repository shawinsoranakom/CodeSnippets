async def aextract_data(
        query: ImfMaritimeChokePointVolumeQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract the raw data from the IMF Port Watch API."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_imf.utils.port_watch_helpers import (
            get_daily_chokepoint_data,
            get_all_daily_chokepoint_activity_data,
        )

        chokepoints = (
            query.chokepoint
            if isinstance(query.chokepoint, list)
            else query.chokepoint.split(",") if query.chokepoint else []
        )

        if not chokepoints:
            try:
                return await get_all_daily_chokepoint_activity_data(
                    start_date=query.start_date, end_date=query.end_date
                )
            except Exception as e:
                raise OpenBBError(e) from e

        results: list = []

        async def get_one(chokepoint_id):
            """Get data for a single chokepoint."""
            data = await get_daily_chokepoint_data(
                chokepoint_id, query.start_date, query.end_date
            )
            if data:
                results.extend(data)

        # Accept both keys and values from CHOKEPOINTS_NAME_TO_ID
        chokepoint_ids: list = []
        for chokepoint in chokepoints:
            if chokepoint in CHOKEPOINTS_NAME_TO_ID:
                chokepoint_ids.append(CHOKEPOINTS_NAME_TO_ID[chokepoint])
            elif chokepoint in CHOKEPOINTS_NAME_TO_ID.values() or chokepoint.startswith(
                "chokepoint"
            ):
                chokepoint_ids.append(chokepoint)
            else:
                raise OpenBBError(
                    f"Invalid chokepoint name: {chokepoint}. Expected one of {list(CHOKEPOINTS_NAME_TO_ID.keys())}."
                )

        tasks = [
            get_one(chokepoint_id) for chokepoint_id in chokepoint_ids if chokepoint_id
        ]

        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        for task_result in task_results:
            if isinstance(task_result, Exception):
                raise OpenBBError(task_result)

        if not results:
            raise OpenBBError("The response was returned empty with no error message.")

        return results