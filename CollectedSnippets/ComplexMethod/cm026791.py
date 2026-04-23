def on_message(self, device: YoLinkDevice, msg_data: dict[str, Any]) -> None:
        """On YoLink home message received."""
        if self._entry.state is not ConfigEntryState.LOADED or not (
            device_coordinator := self._entry.runtime_data.device_coordinators.get(
                device.device_id
            )
        ):
            return

        device_coordinator.dev_online = True
        if (loraInfo := msg_data.get(ATTR_LORA_INFO)) is not None:
            device_coordinator.dev_net_type = loraInfo.get("devNetType")
        device_coordinator.async_set_updated_data(msg_data)
        # handling events
        if (
            device_coordinator.device.device_type
            in [ATTR_DEVICE_SMART_REMOTER, ATTR_DEVICE_SWITCH]
            and msg_data.get("event") is not None
        ):
            device_registry = dr.async_get(self._hass)
            device_entry = device_registry.async_get_device(
                identifiers={(DOMAIN, device_coordinator.device.device_id)}
            )
            if device_entry is None:
                return
            key_press_type = None
            if msg_data["event"]["type"] == "Press":
                key_press_type = CONF_SHORT_PRESS
            else:
                key_press_type = CONF_LONG_PRESS
            button_idx = msg_data["event"]["keyMask"]
            event_data = {
                "type": f"button_{button_idx}_{key_press_type}",
                "device_id": device_entry.id,
            }
            self._hass.bus.async_fire(YOLINK_EVENT, event_data)