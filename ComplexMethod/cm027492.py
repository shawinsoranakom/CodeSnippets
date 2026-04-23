async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow start."""
        errors: dict[str, str] = {}

        if user_input is not None:
            key = user_input["device"]
            discovery = self.devices[key]
            self.category = discovery.description.category
            self.hkid = discovery.description.id
            self.model = getattr(discovery.description, "model", BLE_DEFAULT_NAME)
            self.name = discovery.description.name or BLE_DEFAULT_NAME

            await self.async_set_unique_id(
                normalize_hkid(self.hkid), raise_on_progress=False
            )

            return await self.async_step_pair()

        if self.controller is None:
            await self._async_setup_controller()

        assert self.controller

        self.devices = {}

        async for discovery in self.controller.async_discover():
            if discovery.paired:
                continue
            self.devices[discovery.description.name] = discovery

        if not self.devices:
            return self.async_abort(reason="no_devices")

        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required("device"): vol.In(
                        {
                            key: (
                                f"{key} ({formatted_category(discovery.description.category)})"
                            )
                            for key, discovery in self.devices.items()
                        }
                    )
                }
            ),
        )