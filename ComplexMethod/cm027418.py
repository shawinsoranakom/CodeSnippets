async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        if (
            user_input is not None
            and self.discovered_hubs is not None
            and user_input[CONF_ID] in self.discovered_hubs
        ):
            return await self.async_create(self.discovered_hubs[user_input[CONF_ID]])

        # Already configured hosts
        already_configured = {
            entry.unique_id for entry in self._async_current_entries()
        }

        hubs: list[aiopulse.Hub] = []
        with suppress(TimeoutError):
            async with timeout(5):
                hubs = [
                    hub
                    async for hub in aiopulse.Hub.discover()
                    if hub.id not in already_configured
                ]

        if not hubs:
            return self.async_abort(reason="no_devices_found")

        if len(hubs) == 1:
            return await self.async_create(hubs[0])

        self.discovered_hubs = {hub.id: hub for hub in hubs}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ID): vol.In(
                        {hub.id: f"{hub.id} {hub.host}" for hub in hubs}
                    )
                }
            ),
        )