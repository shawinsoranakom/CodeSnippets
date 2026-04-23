def _forecast(self, hourly: bool) -> list[Forecast]:
        """Return the forecast array."""
        if hourly:
            me_forecast = self.coordinator.data.hourly_forecast
        else:
            me_forecast = self.coordinator.data.daily_forecast
        required_keys = {"temperature", "datetime"}

        ha_forecast: list[Forecast] = []

        for item in me_forecast:
            if not set(item).issuperset(required_keys):
                continue
            ha_item: Forecast = cast(
                Forecast,
                {
                    k: item[v]
                    for k, v in FORECAST_MAP.items()
                    if item.get(v) is not None
                },
            )
            # Convert condition
            if item.get("condition"):
                ha_item[ATTR_FORECAST_CONDITION] = format_condition(item["condition"])
            # Convert timestamp to UTC string
            if item.get("datetime"):
                ha_item[ATTR_FORECAST_TIME] = dt_util.as_utc(
                    item["datetime"]
                ).isoformat()
            ha_forecast.append(ha_item)
        return ha_forecast