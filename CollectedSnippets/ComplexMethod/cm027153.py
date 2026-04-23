async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            new_filter: list[str] = user_input.get(CONF_MAC_FILTER, [])

            # Remove entities for devices no longer in the allow-list
            if new_filter:
                entity_registry = er.async_get(self.hass)
                for reg_entry in er.async_entries_for_config_entry(
                    entity_registry, self.config_entry.entry_id
                ):
                    if (
                        reg_entry.domain == DEVICE_TRACKER_DOMAIN
                        and reg_entry.unique_id not in new_filter
                    ):
                        entity_registry.async_remove(reg_entry.entity_id)

            return self.async_create_entry(data={CONF_MAC_FILTER: new_filter})

        coordinator = self.config_entry.runtime_data
        current_filter: list[str] = self.config_entry.options.get(CONF_MAC_FILTER, [])

        # Build client dict from active clients
        clients: dict[str, str] = {
            mac: f"{client[API_CLIENT_HOSTNAME]} ({mac})"
            for mac, client in coordinator.data[KEY_SYS_CLIENTS].items()
        }

        # Preserve previously selected but now-offline clients
        clients |= {
            mac: f"Unknown ({mac})" for mac in current_filter if mac not in clients
        }

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_MAC_FILTER,
                        default=current_filter,
                    ): cv.multi_select(
                        dict(sorted(clients.items(), key=operator.itemgetter(1)))
                    ),
                }
            ),
        )