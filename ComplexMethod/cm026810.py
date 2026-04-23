async def async_handle_homekit_unpair(service: ServiceCall) -> None:
        """Handle unpair HomeKit service call."""
        referenced = async_extract_referenced_entity_ids(
            hass, TargetSelection(service.data)
        )
        dev_reg = dr.async_get(hass)
        for device_id in referenced.referenced_devices:
            if not (dev_reg_ent := dev_reg.async_get(device_id)):
                raise HomeAssistantError(f"No device found for device id: {device_id}")
            macs = [
                cval
                for ctype, cval in dev_reg_ent.connections
                if ctype == dr.CONNECTION_NETWORK_MAC
            ]
            matching_instances = [
                homekit
                for homekit in _async_all_homekit_instances(hass)
                if homekit.driver and dr.format_mac(homekit.driver.state.mac) in macs
            ]
            if not matching_instances:
                raise HomeAssistantError(
                    f"No homekit accessory found for device id: {device_id}"
                )
            for homekit in matching_instances:
                homekit.async_unpair()