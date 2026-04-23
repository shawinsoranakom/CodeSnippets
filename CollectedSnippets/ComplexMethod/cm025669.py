def _forecast(
        self,
        nws_forecast: list[dict[str, Any]],
        mode: str,
    ) -> list[Forecast]:
        """Return forecast."""
        if nws_forecast is None:
            return []
        forecast: list[Forecast] = []
        for forecast_entry in nws_forecast:
            data: Forecast = {
                ATTR_FORECAST_TIME: cast(str, forecast_entry.get("startTime")),
            }

            if (temp := forecast_entry.get("temperature")) is not None:
                data[ATTR_FORECAST_NATIVE_TEMP] = TemperatureConverter.convert(
                    temp, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS
                )
            else:
                data[ATTR_FORECAST_NATIVE_TEMP] = None

            data[ATTR_FORECAST_PRECIPITATION_PROBABILITY] = forecast_entry.get(
                "probabilityOfPrecipitation"
            )

            if (dewp := forecast_entry.get("dewpoint")) is not None:
                data[ATTR_FORECAST_NATIVE_DEW_POINT] = TemperatureConverter.convert(
                    dewp, UnitOfTemperature.FAHRENHEIT, UnitOfTemperature.CELSIUS
                )
            else:
                data[ATTR_FORECAST_NATIVE_DEW_POINT] = None

            data[ATTR_FORECAST_HUMIDITY] = forecast_entry.get("relativeHumidity")

            if mode == DAYNIGHT:
                data[ATTR_FORECAST_IS_DAYTIME] = forecast_entry.get("isDaytime")

            time = forecast_entry.get("iconTime")
            weather = forecast_entry.get("iconWeather")
            data[ATTR_FORECAST_CONDITION] = (
                convert_condition(time, weather) if time and weather else None
            )

            data[ATTR_FORECAST_WIND_BEARING] = forecast_entry.get("windBearing")
            wind_speed = forecast_entry.get("windSpeedAvg")
            if wind_speed is not None:
                data[ATTR_FORECAST_NATIVE_WIND_SPEED] = SpeedConverter.convert(
                    wind_speed,
                    UnitOfSpeed.MILES_PER_HOUR,
                    UnitOfSpeed.KILOMETERS_PER_HOUR,
                )
            else:
                data[ATTR_FORECAST_NATIVE_WIND_SPEED] = None
            forecast.append(data)
        return forecast