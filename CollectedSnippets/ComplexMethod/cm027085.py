async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the step to pick discovered device."""
        errors: dict[str, str] = {}
        device_adv: SwitchBotAdvertisement | None = None
        if user_input is not None:
            device_adv = self._discovered_advs[user_input[CONF_ADDRESS]]
            await self._async_set_device(device_adv)
            if device_adv.data.get("modelName") in ENCRYPTED_MODELS:
                return await self.async_step_encrypted_choose_method()
            if device_adv.data["isEncrypted"]:
                return await self.async_step_password()
            return await self._async_create_entry_from_discovery(user_input)

        self._async_discover_devices()
        if len(self._discovered_advs) == 1:
            # If there is only one device we can ask for a password
            # or simply confirm it
            device_adv = list(self._discovered_advs.values())[0]
            await self._async_set_device(device_adv)
            if device_adv.data.get("modelName") in ENCRYPTED_MODELS:
                return await self.async_step_encrypted_choose_method()
            if device_adv.data["isEncrypted"]:
                return await self.async_step_password()
            return await self.async_step_confirm()

        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDRESS): vol.In(
                        {
                            address: name_from_discovery(parsed)
                            for address, parsed in self._discovered_advs.items()
                        }
                    ),
                }
            ),
            errors=errors,
        )