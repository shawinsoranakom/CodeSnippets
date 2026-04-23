async def async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast."""
        # Using hourly data to create daily summaries, since daily data is not provided directly
        if not self.coordinator.data:
            return None

        forecasts_by_date = defaultdict(list)
        for timestamp in self.coordinator.data.forecast_timestamps:
            date = datetime.fromisoformat(timestamp.datetime).date()
            forecasts_by_date[date].append(timestamp)

        daily_forecasts = []
        for date in sorted(forecasts_by_date.keys()):
            day_forecasts = forecasts_by_date[date]
            if not day_forecasts:
                continue

            temps = [
                ts.temperature for ts in day_forecasts if ts.temperature is not None
            ]
            max_temp = max(temps) if temps else None
            min_temp = min(temps) if temps else None

            midday_forecast = min(
                day_forecasts,
                key=lambda ts: abs(datetime.fromisoformat(ts.datetime).hour - 12),
            )

            daily_forecast = Forecast(
                datetime=day_forecasts[0].datetime,
                native_temperature=max_temp,
                native_templow=min_temp,
                native_apparent_temperature=midday_forecast.apparent_temperature,
                condition=midday_forecast.condition,
                # Calculate precipitation: sum if any values, else None
                native_precipitation=(
                    sum(
                        ts.precipitation
                        for ts in day_forecasts
                        if ts.precipitation is not None
                    )
                    if any(ts.precipitation is not None for ts in day_forecasts)
                    else None
                ),
                precipitation_probability=None,
                native_wind_speed=midday_forecast.wind_speed,
                wind_bearing=midday_forecast.wind_bearing,
                cloud_coverage=midday_forecast.cloud_coverage,
            )
            daily_forecasts.append(daily_forecast)

        return daily_forecasts