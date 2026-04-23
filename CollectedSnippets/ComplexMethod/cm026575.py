async def _async_update_data(self) -> dict[str, TibberHomeData]:
        """Update data via API and return per-home data for sensors."""
        tibber_connection = await self._async_get_client()
        active_homes = tibber_connection.get_homes(only_active=True)

        now = dt_util.now()
        today_start = dt_util.start_of_local_day(now)
        today_end = today_start + timedelta(days=1)
        tomorrow_start = today_end
        tomorrow_end = tomorrow_start + timedelta(days=1)

        def _has_prices_today(home: tibber.TibberHome) -> bool:
            """Return True if the home has any prices today."""
            for start in home.price_total:
                start_dt = dt_util.as_local(datetime.fromisoformat(str(start)))
                if today_start <= start_dt < today_end:
                    return True
            return False

        def _has_prices_tomorrow(home: tibber.TibberHome) -> bool:
            """Return True if the home has any prices tomorrow."""
            for start in home.price_total:
                start_dt = dt_util.as_local(datetime.fromisoformat(str(start)))
                if tomorrow_start <= start_dt < tomorrow_end:
                    return True
            return False

        def _needs_update(home: tibber.TibberHome) -> bool:
            """Return True if the home needs to be updated."""
            if not _has_prices_today(home):
                return True
            if _has_prices_tomorrow(home):
                return False
            if (today_end - now).total_seconds() < (
                self._tomorrow_price_poll_threshold_seconds
            ):
                return True
            return False

        homes_to_update = [home for home in active_homes if _needs_update(home)]

        try:
            if homes_to_update:
                await asyncio.gather(
                    *(home.update_info_and_price_info() for home in homes_to_update)
                )
        except tibber.RetryableHttpExceptionError as err:
            raise UpdateFailed(f"Error communicating with API ({err.status})") from err
        except tibber.FatalHttpExceptionError as err:
            raise UpdateFailed(f"Error communicating with API ({err.status})") from err

        result = {home.home_id: _build_home_data(home) for home in active_homes}

        self.update_interval = self._time_until_next_15_minute()
        return result