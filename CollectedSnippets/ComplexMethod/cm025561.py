async def async_fetch_options(self) -> None:
        """Fetch options from the API."""
        setting = self.appliance.settings.get(cast(SettingKey, self.bsh_key))
        if (
            not setting
            or not setting.constraints
            or not setting.constraints.allowed_values
        ):
            setting = await self.coordinator.client.get_setting(
                self.appliance.info.ha_id,
                setting_key=cast(SettingKey, self.bsh_key),
            )

        if setting and setting.constraints and setting.constraints.allowed_values:
            self._original_option_keys = set(setting.constraints.allowed_values)
            self._attr_options = [
                self.entity_description.values_translation_key[option]
                for option in self._original_option_keys
                if option is not None
                and option in self.entity_description.values_translation_key
            ]