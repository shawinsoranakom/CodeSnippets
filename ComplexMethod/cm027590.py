async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Confirm setup."""
        if user_input is None and onboarding.async_is_onboarded(self.hass):
            self._set_confirm_only()
            return self.async_show_form(step_id="confirm")

        if self.source == config_entries.SOURCE_USER:
            # Get current discovered entries.
            in_progress = self._async_in_progress()

            if not (has_devices := bool(in_progress)):
                discovery_result = self._discovery_function(self.hass)
                if isinstance(discovery_result, bool):
                    has_devices = discovery_result
                else:
                    has_devices = await cast("asyncio.Future[bool]", discovery_result)

            if not has_devices:
                return self.async_abort(reason="no_devices_found")

            # Cancel the discovered one.
            for flow in in_progress:
                self.hass.config_entries.flow.async_abort(flow["flow_id"])

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title=self._title, data={})