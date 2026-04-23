async def _async_update_data(self) -> dict[str, Any]:
        """Get the latest data from the Glances REST API."""
        try:
            data = await self.api.get_ha_sensor_data()
        except exceptions.GlancesApiAuthorizationError as err:
            raise ConfigEntryAuthFailed from err
        except exceptions.GlancesApiError as err:
            raise UpdateFailed from err
        # Update computed values
        uptime: datetime | None = None
        up_duration: timedelta | None = None
        if "uptime" in data and (up_duration := parse_duration(data["uptime"])):
            uptime = self.data["computed"]["uptime"] if self.data else None
            # Update uptime if previous value is None or previous uptime is bigger than
            # new uptime (i.e. server restarted)
            if uptime is None or self.data["computed"]["uptime_duration"] > up_duration:
                uptime = utcnow() - up_duration
        data["computed"] = {"uptime_duration": up_duration, "uptime": uptime}
        return data or {}