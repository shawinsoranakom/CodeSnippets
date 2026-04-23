async def async_step_site(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select site to control."""
        if user_input is not None:
            unique_id = user_input[CONF_SITE_ID]
            self.config[CONF_SITE_ID] = self.sites[unique_id].name

            config_entry = await self.async_set_unique_id(unique_id)
            abort_reason = "configuration_updated"

            if self.source == SOURCE_REAUTH:
                config_entry = self._get_reauth_entry()
                abort_reason = "reauth_successful"

            if config_entry:
                if (
                    config_entry.state is ConfigEntryState.LOADED
                    and (hub := config_entry.runtime_data)
                    and hub.available
                ):
                    return self.async_abort(reason="already_configured")

                return self.async_update_reload_and_abort(
                    config_entry, data=self.config, reason=abort_reason
                )

            site_nice_name = self.sites[unique_id].description
            return self.async_create_entry(title=site_nice_name, data=self.config)

        if len(self.sites.values()) == 1:
            return await self.async_step_site({CONF_SITE_ID: next(iter(self.sites))})

        site_names = {site.site_id: site.description for site in self.sites.values()}
        return self.async_show_form(
            step_id="site",
            data_schema=vol.Schema({vol.Required(CONF_SITE_ID): vol.In(site_names)}),
        )