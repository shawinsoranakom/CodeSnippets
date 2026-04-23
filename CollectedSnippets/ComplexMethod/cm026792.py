async def _async_invoke_device(self, state: str) -> None:
        """Call setState api to change valve state."""
        if (
            self.coordinator.device.is_support_mode_switching()
            and self.coordinator.dev_net_type == ATTR_DEVICE_MODEL_A
        ):
            raise HomeAssistantError(
                translation_domain=DOMAIN, translation_key="valve_inoperable_currently"
            )
        if (
            self.coordinator.device.device_type
            == ATTR_DEVICE_MULTI_WATER_METER_CONTROLLER
        ):
            channel_index = self.entity_description.channel_index
            if channel_index is not None:
                await self.call_device(
                    ClientRequest("setState", {"valves": {str(channel_index): state}})
                )
        if self.coordinator.device.device_type == ATTR_DEVICE_SPRINKLER:
            await self.call_device(
                ClientRequest(
                    "setManualWater", {"state": "start" if state == "open" else "stop"}
                )
            )
        if self.coordinator.device.device_type == ATTR_DEVICE_SPRINKLER_V2:
            await self.call_device(
                ClientRequest("setState", {"running": state == "open"})
            )
        else:
            await self.call_device(ClientRequest("setState", {"valve": state}))
        self._attr_is_closed = state == "close"
        self.async_write_ha_state()