def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        if self.coordinator.data.hourly is None:
            return None

        forecasts: list[Forecast] = []

        # Can have data in the past: https://github.com/open-meteo/open-meteo/issues/699
        today = dt_util.utcnow()

        hourly = self.coordinator.data.hourly
        for index, _datetime in enumerate(self.coordinator.data.hourly.time):
            if _datetime.tzinfo is None:
                _datetime = _datetime.replace(tzinfo=dt_util.UTC)
            if _datetime < today:
                continue

            forecast = Forecast(
                datetime=_datetime.isoformat(),
            )

            if hourly.weather_code is not None:
                forecast[ATTR_FORECAST_CONDITION] = WMO_TO_HA_CONDITION_MAP.get(
                    hourly.weather_code[index]
                )

            if hourly.precipitation is not None:
                forecast[ATTR_FORECAST_NATIVE_PRECIPITATION] = hourly.precipitation[
                    index
                ]

            if hourly.temperature_2m is not None:
                forecast[ATTR_FORECAST_NATIVE_TEMP] = hourly.temperature_2m[index]

            forecasts.append(forecast)

        return forecasts