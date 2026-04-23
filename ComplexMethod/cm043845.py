async def aextract_data(
        query: DeribitFuturesCurveQueryParams,
        credentials: dict[str, str] | None,
        **kwargs: Any,
    ) -> list:
        """Extract the raw data."""
        # pylint: disable=import-outside-toplevel
        import asyncio  # noqa
        from openbb_deribit.utils.helpers import (
            get_futures_curve_symbols,
            get_ticker_data,
            get_futures_curve_by_hours_ago,
        )

        try:
            symbols = await get_futures_curve_symbols(query.symbol)
            tasks = [get_ticker_data(s) for s in symbols]
            data = await asyncio.gather(*tasks, return_exceptions=True)

            if query.hours_ago is not None:
                num_hours = query.hours_ago

                hours_ago = (
                    [int(d) for d in num_hours.split(",")]
                    if isinstance(num_hours, str)
                    else [int(num_hours)] if isinstance(num_hours, int) else num_hours
                )

                for hours in hours_ago:
                    hours_data = await get_futures_curve_by_hours_ago(
                        query.symbol, hours
                    )
                    if hours_data:
                        data.extend(hours_data)
            return data
        except Exception as e:  # pylint: disable=broad-except
            raise OpenBBError(
                f"Failed to get futures curve -> {e.__class__.__name__ if hasattr(e, '__class__') else e}: {e.args}"
            ) from e