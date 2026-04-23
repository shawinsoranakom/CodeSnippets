def _async_device_event_handler(self, event_data: dict[str, Any]) -> None:
        """Handle device events."""
        events: list[dict[str, Any]] = event_data["events"]
        for event in events:
            # filter out button events as they are triggered by button entities
            component = event.get("component")
            if component is not None and component.startswith("button"):
                continue

            event_type = event.get("event")
            if event_type is None:
                continue

            for event_callback in self._event_listeners:
                event_callback(event)

            if event_type in ("component_added", "component_removed", "config_changed"):
                self.update_sleep_period()
                LOGGER.info(
                    "Config for %s changed, reloading entry in %s seconds",
                    self.name,
                    ENTRY_RELOAD_COOLDOWN,
                )
                self._debounced_reload.async_schedule_call()
            elif event_type in RPC_INPUTS_EVENTS_TYPES:
                for event_callback in self._input_event_listeners:
                    event_callback(event)
                self.hass.bus.async_fire(
                    EVENT_SHELLY_CLICK,
                    {
                        ATTR_DEVICE_ID: self.device_id,
                        ATTR_DEVICE: self.device.hostname,
                        ATTR_CHANNEL: event["id"] + 1,
                        ATTR_CLICK_TYPE: event["event"],
                        ATTR_GENERATION: 2,
                    },
                )
            elif event_type in (OTA_BEGIN, OTA_ERROR, OTA_PROGRESS, OTA_SUCCESS):
                for event_callback in self._ota_event_listeners:
                    event_callback(event)