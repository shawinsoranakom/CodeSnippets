def _on_data_update(self) -> None:
        """Handle data updates and process dynamic entity management."""
        if self.data is not None:
            self._async_add_remove_devices()
            if any(
                mower_data.capabilities.stay_out_zones
                for mower_data in self.data.values()
            ):
                self._async_add_remove_stay_out_zones()
            if any(
                mower_data.capabilities.work_areas for mower_data in self.data.values()
            ):
                self._async_add_remove_work_areas()
            if (
                not self._should_poll()
                and self.update_interval is not None
                and self.websocket_alive
            ):
                _LOGGER.debug("All mowers inactive and websocket alive: stop polling")
                self.update_interval = None
            if self.update_interval is None and self._should_poll():
                _LOGGER.debug(
                    "Polling re-enabled via WebSocket: at least one mower active"
                )
                self.update_interval = SCAN_INTERVAL
                self.hass.async_create_task(self.async_request_refresh())