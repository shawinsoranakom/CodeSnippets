def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        if self.coordinator.data.daily is None:
            return None

        forecasts: list[Forecast] = []

        daily = self.coordinator.data.daily
        for index, date in enumerate(self.coordinator.data.daily.time):
            _datetime = datetime.combine(date=date, time=time(0), tzinfo=dt_util.UTC)
            forecast = Forecast(
                datetime=_datetime.isoformat(),
            )

            if daily.weathercode is not None:
                forecast[ATTR_FORECAST_CONDITION] = WMO_TO_HA_CONDITION_MAP.get(
                    daily.weathercode[index]
                )

            if daily.precipitation_sum is not None:
                forecast[ATTR_FORECAST_NATIVE_PRECIPITATION] = daily.precipitation_sum[
                    index
                ]

            if daily.temperature_2m_max is not None:
                forecast[ATTR_FORECAST_NATIVE_TEMP] = daily.temperature_2m_max[index]

            if daily.temperature_2m_min is not None:
                forecast[ATTR_FORECAST_NATIVE_TEMP_LOW] = daily.temperature_2m_min[
                    index
                ]

            if daily.wind_direction_10m_dominant is not None:
                forecast[ATTR_FORECAST_WIND_BEARING] = (
                    daily.wind_direction_10m_dominant[index]
                )

            if daily.wind_speed_10m_max is not None:
                forecast[ATTR_FORECAST_NATIVE_WIND_SPEED] = daily.wind_speed_10m_max[
                    index
                ]

            forecasts.append(forecast)

        return forecasts