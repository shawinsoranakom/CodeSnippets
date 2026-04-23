async def async_set_level(self, brightness: int) -> None:
        """Set lamp brightness via supported levels."""
        levels = (
            self.get_attribute_value(
                Capability.SAMSUNG_CE_LAMP, Attribute.SUPPORTED_BRIGHTNESS_LEVEL
            )
            or []
        )
        # remove 'off' for brightness mapping
        if "off" in levels:
            levels = [level for level in levels if level != "off"]
        level = percentage_to_ordered_list_item(
            levels, int(round(brightness * 100 / 255))
        )
        await self.execute_device_command(
            Capability.SAMSUNG_CE_LAMP,
            Command.SET_BRIGHTNESS_LEVEL,
            argument=level,
        )
        # turn on switch separately if needed
        if (
            self.supports_capability(Capability.SWITCH)
            and not self.is_on
            and brightness > 0
        ):
            await self.execute_device_command(Capability.SWITCH, Command.ON)