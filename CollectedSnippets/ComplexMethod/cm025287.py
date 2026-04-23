def _forecast(self, forecast_type: str) -> list[Forecast] | None:
        """Return the forecast."""
        # Check if forecasts are available
        raw_forecasts = (
            self.coordinator.data.get(self._config_entry.entry_id, {})
            .get(FORECASTS, {})
            .get(forecast_type)
        )
        if not raw_forecasts:
            return None

        forecasts: list[Forecast] = []
        max_forecasts = MAX_FORECASTS[forecast_type]
        forecast_count = 0

        # Convert utcnow to local to be compatible with tests
        today = dt_util.as_local(dt_util.utcnow()).date()

        # Set default values (in cases where keys don't exist), None will be
        # returned. Override properties per forecast type as needed
        for forecast in raw_forecasts:
            forecast_dt = dt_util.parse_datetime(forecast[TMRW_ATTR_TIMESTAMP])

            # Throw out past data
            if forecast_dt is None or dt_util.as_local(forecast_dt).date() < today:
                continue

            values = forecast["values"]
            use_datetime = True

            condition = values.get(TMRW_ATTR_CONDITION)
            precipitation = values.get(TMRW_ATTR_PRECIPITATION)
            precipitation_probability = values.get(TMRW_ATTR_PRECIPITATION_PROBABILITY)

            try:
                precipitation_probability = round(precipitation_probability)
            except TypeError:
                precipitation_probability = None

            temp = values.get(TMRW_ATTR_TEMPERATURE_HIGH)
            temp_low = None
            dew_point = values.get(TMRW_ATTR_DEW_POINT)
            humidity = values.get(TMRW_ATTR_HUMIDITY)

            wind_direction = values.get(TMRW_ATTR_WIND_DIRECTION)
            wind_speed = values.get(TMRW_ATTR_WIND_SPEED)

            if forecast_type == DAILY:
                use_datetime = False
                temp_low = values.get(TMRW_ATTR_TEMPERATURE_LOW)
                if precipitation:
                    precipitation = precipitation * 24
            elif forecast_type == NOWCAST:
                # Precipitation is forecasted in CONF_TIMESTEP increments but in a
                # per hour rate, so value needs to be converted to an amount.
                if precipitation:
                    precipitation = (
                        precipitation / 60 * self._config_entry.options[CONF_TIMESTEP]
                    )

            forecasts.append(
                self._forecast_dict(
                    forecast_dt,
                    use_datetime,
                    condition,
                    precipitation,
                    precipitation_probability,
                    temp,
                    temp_low,
                    humidity,
                    dew_point,
                    wind_direction,
                    wind_speed,
                )
            )

            forecast_count += 1
            if forecast_count == max_forecasts:
                break

        return forecasts