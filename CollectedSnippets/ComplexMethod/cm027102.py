def _get_forecast_data(
        self, forecast_data: list[SMHIForecast] | None, forecast_type: str
    ) -> list[Forecast] | None:
        """Get forecast data."""
        if forecast_data is None or len(forecast_data) < 3:
            return None

        data: list[Forecast] = []

        for forecast in forecast_data[1:]:
            condition = CONDITION_MAP.get(forecast["symbol"])
            if condition == ATTR_CONDITION_SUNNY and not sun.is_up(
                self.hass, forecast["valid_time"]
            ):
                condition = ATTR_CONDITION_CLEAR_NIGHT

            new_forecast = Forecast(
                {
                    ATTR_FORECAST_TIME: forecast["valid_time"].isoformat(),
                    ATTR_FORECAST_NATIVE_TEMP: forecast["temperature_max"],
                    ATTR_FORECAST_NATIVE_TEMP_LOW: forecast["temperature_min"],
                    ATTR_FORECAST_NATIVE_PRECIPITATION: forecast.get(
                        "total_precipitation"
                    )
                    or forecast["mean_precipitation"],
                    ATTR_FORECAST_CONDITION: condition,
                    ATTR_FORECAST_NATIVE_PRESSURE: forecast["pressure"],
                    ATTR_FORECAST_WIND_BEARING: forecast["wind_direction"],
                    ATTR_FORECAST_NATIVE_WIND_SPEED: forecast["wind_speed"],
                    ATTR_FORECAST_HUMIDITY: forecast["humidity"],
                    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: forecast["wind_gust"],
                    ATTR_FORECAST_CLOUD_COVERAGE: forecast["total_cloud"],
                }
            )
            if forecast_type == "twice_daily":
                new_forecast[ATTR_FORECAST_IS_DAYTIME] = False
                if forecast["valid_time"].hour == 12:
                    new_forecast[ATTR_FORECAST_IS_DAYTIME] = True

            data.append(new_forecast)

        return data