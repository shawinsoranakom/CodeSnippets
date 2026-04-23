def update_price_data(self) -> dict[str, dict[str, Any]]:
        """Update callback."""

        result: dict[str, dict[str, Any]] = {
            "current": {},
            "descriptors": {},
            "forecasts": {},
            "grid": {},
        }
        try:
            data = self._api.get_current_prices(
                self.site_id,
                next=288,
                _request_timeout=REQUEST_TIMEOUT,
            )
            intervals = [interval.actual_instance for interval in data]
        except ApiException as api_exception:
            raise UpdateFailed("Missing price data, skipping update") from api_exception

        current = [interval for interval in intervals if is_current(interval)]
        forecasts = [interval for interval in intervals if is_forecast(interval)]
        general = [interval for interval in current if is_general(interval)]

        if len(general) == 0:
            raise UpdateFailed("No general channel configured")

        result["current"]["general"] = general[0]
        result["descriptors"]["general"] = normalize_descriptor(general[0].descriptor)
        result["forecasts"]["general"] = [
            interval for interval in forecasts if is_general(interval)
        ]
        result["grid"]["renewables"] = round(general[0].renewables)
        result["grid"]["price_spike"] = general[0].spike_status.value
        tariff_information = general[0].tariff_information
        if tariff_information:
            result["grid"]["demand_window"] = tariff_information.demand_window

        controlled_load = [
            interval for interval in current if is_controlled_load(interval)
        ]
        if controlled_load:
            result["current"]["controlled_load"] = controlled_load[0]
            result["descriptors"]["controlled_load"] = normalize_descriptor(
                controlled_load[0].descriptor
            )
            result["forecasts"]["controlled_load"] = [
                interval for interval in forecasts if is_controlled_load(interval)
            ]

        feed_in = [interval for interval in current if is_feed_in(interval)]
        if feed_in:
            result["current"]["feed_in"] = feed_in[0]
            result["descriptors"]["feed_in"] = normalize_descriptor(
                feed_in[0].descriptor
            )
            result["forecasts"]["feed_in"] = [
                interval for interval in forecasts if is_feed_in(interval)
            ]

        LOGGER.debug("Fetched new Amber data: %s", intervals)
        return result