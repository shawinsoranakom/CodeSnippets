async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Subentry user flow."""
        config_entry: XboxConfigEntry = self._get_entry()
        if config_entry.state is not ConfigEntryState.LOADED:
            return self.async_abort(reason="config_entry_not_loaded")

        client = config_entry.runtime_data.presence.client
        friends_list = await client.people.get_friends_own()

        if user_input is not None:
            config_entries = self.hass.config_entries.async_entries(DOMAIN)
            if user_input[CONF_XUID] in {entry.unique_id for entry in config_entries}:
                return self.async_abort(reason="already_configured_as_entry")
            for entry in config_entries:
                if user_input[CONF_XUID] in {
                    subentry.unique_id for subentry in entry.subentries.values()
                }:
                    return self.async_abort(reason="already_configured")

            return self.async_create_entry(
                title=next(
                    f.gamertag
                    for f in friends_list.people
                    if f.xuid == user_input[CONF_XUID]
                ),
                data={},
                unique_id=user_input[CONF_XUID],
            )

        if not friends_list.people:
            return self.async_abort(reason="no_friends")

        options = [
            SelectOptionDict(
                value=friend.xuid,
                label=friend.gamertag,
            )
            for friend in friends_list.people
        ]

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                vol.Schema(
                    {
                        vol.Required(CONF_XUID): SelectSelector(
                            SelectSelectorConfig(options=options)
                        )
                    }
                ),
                user_input,
            ),
        )