async def async_step_stop(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Handle the stop selection step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            stop_id = user_input[CONF_STOP_ID]
            self.data[CONF_STOP_ID] = stop_id
            stop_name = self.stops.get(stop_id, stop_id)
            self.data[CONF_STOP_NAME] = stop_name

            unique_id = f"bus_{self.data[CONF_ROUTE]}_{stop_id}"

            # Check for duplicate subentries across all entries
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                for subentry in entry.subentries.values():
                    if subentry.unique_id == unique_id:
                        return self.async_abort(reason="already_configured")

            # Test connection to real-time feed
            try:
                await self._async_test_connection()
            except MTAFeedError:
                errors["base"] = "cannot_connect"
            else:
                title = f"{self.data[CONF_ROUTE]} - {stop_name}"
                return self.async_create_entry(
                    title=title,
                    data=self.data,
                    unique_id=unique_id,
                )

        stop_options = [
            SelectOptionDict(value=stop_id, label=stop_name)
            for stop_id, stop_name in sorted(self.stops.items(), key=lambda x: x[1])
        ]

        return self.async_show_form(
            step_id="stop",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STOP_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=stop_options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"route": self.data[CONF_ROUTE]},
        )