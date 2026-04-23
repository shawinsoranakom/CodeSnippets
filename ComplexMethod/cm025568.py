async def async_fetch_power_off_state(self) -> None:
        """Fetch the power off state."""
        data = self.appliance.settings[SettingKey.BSH_COMMON_POWER_STATE]

        if not data.constraints or not data.constraints.allowed_values:
            try:
                data = await self.coordinator.client.get_setting(
                    self.appliance.info.ha_id,
                    setting_key=SettingKey.BSH_COMMON_POWER_STATE,
                )
            except HomeConnectError as err:
                _LOGGER.error("An error occurred fetching the power settings: %s", err)
                return
        if not data.constraints or not data.constraints.allowed_values:
            return

        if BSH_POWER_OFF in data.constraints.allowed_values:
            self.power_off_state = BSH_POWER_OFF
        elif BSH_POWER_STANDBY in data.constraints.allowed_values:
            self.power_off_state = BSH_POWER_STANDBY
        else:
            self.power_off_state = None