async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        data: dict[str, Any] = {}
        # If we are refreshing because of a new config entry that's not already in our
        # data, we do a partial refresh to avoid wasted API calls.
        if self.data and any(
            entry_id not in self.data for entry_id in self.entry_id_to_location_dict
        ):
            data = self.data

        LOGGER.debug(
            "Fetching data for %s entries",
            len(set(self.entry_id_to_location_dict) - set(data)),
        )
        for entry_id, location in self.entry_id_to_location_dict.items():
            if entry_id in data:
                continue
            entry = self.hass.config_entries.async_get_entry(entry_id)
            assert entry
            try:
                data[entry_id] = await self._api.realtime_and_all_forecasts(
                    [
                        # Weather
                        TMRW_ATTR_TEMPERATURE,
                        TMRW_ATTR_HUMIDITY,
                        TMRW_ATTR_PRESSURE,
                        TMRW_ATTR_WIND_SPEED,
                        TMRW_ATTR_WIND_DIRECTION,
                        TMRW_ATTR_CONDITION,
                        TMRW_ATTR_VISIBILITY,
                        TMRW_ATTR_OZONE,
                        TMRW_ATTR_WIND_GUST,
                        TMRW_ATTR_CLOUD_COVER,
                        TMRW_ATTR_PRECIPITATION_TYPE,
                        # Sensors
                        TMRW_ATTR_CARBON_MONOXIDE,
                        TMRW_ATTR_CHINA_AQI,
                        TMRW_ATTR_CHINA_HEALTH_CONCERN,
                        TMRW_ATTR_CHINA_PRIMARY_POLLUTANT,
                        TMRW_ATTR_CLOUD_BASE,
                        TMRW_ATTR_CLOUD_CEILING,
                        TMRW_ATTR_CLOUD_COVER,
                        TMRW_ATTR_DEW_POINT,
                        TMRW_ATTR_EPA_AQI,
                        TMRW_ATTR_EPA_HEALTH_CONCERN,
                        TMRW_ATTR_EPA_PRIMARY_POLLUTANT,
                        TMRW_ATTR_FEELS_LIKE,
                        TMRW_ATTR_FIRE_INDEX,
                        TMRW_ATTR_NITROGEN_DIOXIDE,
                        TMRW_ATTR_OZONE,
                        TMRW_ATTR_PARTICULATE_MATTER_10,
                        TMRW_ATTR_PARTICULATE_MATTER_25,
                        TMRW_ATTR_POLLEN_GRASS,
                        TMRW_ATTR_POLLEN_TREE,
                        TMRW_ATTR_POLLEN_WEED,
                        TMRW_ATTR_PRECIPITATION_TYPE,
                        TMRW_ATTR_PRESSURE_SURFACE_LEVEL,
                        TMRW_ATTR_SOLAR_GHI,
                        TMRW_ATTR_SULPHUR_DIOXIDE,
                        TMRW_ATTR_UV_INDEX,
                        TMRW_ATTR_UV_HEALTH_CONCERN,
                        TMRW_ATTR_WIND_GUST,
                    ],
                    [
                        TMRW_ATTR_TEMPERATURE_LOW,
                        TMRW_ATTR_TEMPERATURE_HIGH,
                        TMRW_ATTR_DEW_POINT,
                        TMRW_ATTR_HUMIDITY,
                        TMRW_ATTR_WIND_SPEED,
                        TMRW_ATTR_WIND_DIRECTION,
                        TMRW_ATTR_CONDITION,
                        TMRW_ATTR_PRECIPITATION,
                        TMRW_ATTR_PRECIPITATION_PROBABILITY,
                    ],
                    nowcast_timestep=entry.options[CONF_TIMESTEP],
                    location=location,
                )
            except (
                CantConnectException,
                InvalidAPIKeyException,
                RateLimitedException,
                UnknownException,
            ) as error:
                raise UpdateFailed from error

        return data