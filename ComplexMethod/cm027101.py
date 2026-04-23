async def discovery_update(trigger_config: TasmotaTriggerConfig) -> None:
        """Handle discovery update."""
        _LOGGER.debug(
            "Got update for trigger with hash: %s '%s'", discovery_hash, trigger_config
        )
        device_triggers: dict[str, Trigger] = hass.data[DEVICE_TRIGGERS]
        if not trigger_config.is_active:
            # Empty trigger_config: Remove trigger
            _LOGGER.debug("Removing trigger: %s", discovery_hash)
            if discovery_id in device_triggers:
                device_trigger = device_triggers[discovery_id]
                assert device_trigger.tasmota_trigger
                await device_trigger.tasmota_trigger.unsubscribe_topics()
                device_trigger.detach_trigger()
                clear_discovery_hash(hass, discovery_hash)
                if remove_update_signal is not None:
                    remove_update_signal()
            return

        device_trigger = device_triggers[discovery_id]
        assert device_trigger.tasmota_trigger
        if device_trigger.tasmota_trigger.config_same(trigger_config):
            # Unchanged payload: Ignore to avoid unnecessary unsubscribe / subscribe
            _LOGGER.debug("Ignoring unchanged update for: %s", discovery_hash)
            return

        # Non-empty, changed trigger_config: Update trigger
        _LOGGER.debug("Updating trigger: %s", discovery_hash)
        device_trigger.tasmota_trigger.config_update(trigger_config)
        assert remove_update_signal
        await device_trigger.update_tasmota_trigger(
            trigger_config, remove_update_signal
        )
        await device_trigger.arm_tasmota_trigger()
        return