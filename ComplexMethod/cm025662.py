async def async_update_data(self) -> None:
        """Update the data from the SolarEdge Monitoring API."""
        try:
            data = await self.api.get_overview(self.site_id)
            overview = data["overview"]
        except KeyError as ex:
            raise UpdateFailed("Missing overview data, skipping update") from ex

        self.data = {}

        energy_keys = ["lifeTimeData", "lastYearData", "lastMonthData", "lastDayData"]
        for key, value in overview.items():
            if key in energy_keys:
                data = value["energy"]
            elif key == "currentPower":
                data = value["power"]
            else:
                data = value
            self.data[key] = data

        # Sanity check the energy values. SolarEdge API sometimes report "lifetimedata" of zero,
        # while values for last Year, Month and Day energy are still OK.
        # See https://github.com/home-assistant/core/issues/59285 .
        if set(energy_keys).issubset(self.data.keys()):
            for index, key in enumerate(energy_keys, start=1):
                # All coming values in list should be larger than the current value.
                if any(self.data[k] > self.data[key] for k in energy_keys[index:]):
                    LOGGER.warning(
                        "Ignoring invalid energy value %s for %s", self.data[key], key
                    )
                    self.data.pop(key)

        LOGGER.debug("Updated SolarEdge overview: %s", self.data)