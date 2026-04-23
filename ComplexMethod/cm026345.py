async def async_step_select_site(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Second step: present sites and validate selection."""
        assert self._api_token is not None

        if user_input is None:
            site_options = self._build_site_options()
            return self.async_show_form(
                step_id="select_site",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_SITE_ID): SelectSelector(
                            SelectSelectorConfig(
                                options=site_options, mode=SelectSelectorMode.DROPDOWN
                            )
                        )
                    }
                ),
            )

        # User submitted a site selection
        site_id = int(user_input[CONF_SITE_ID])
        # Prevent duplicate entries for the same site
        self._async_abort_entries_match({CONF_SITE_ID: site_id})

        errors: dict[str, str] = {}
        try:
            site = await self._async_validate_selected_site(self._api_token, site_id)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except SiteNotFound:
            errors["base"] = "site_not_found"
        except Exception:  # pragma: no cover - unexpected
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Ensure unique ID per site to avoid duplicates across reloads
            await self.async_set_unique_id(str(site_id), raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"VRM for {site.name}",
                data={CONF_API_TOKEN: self._api_token, CONF_SITE_ID: site_id},
            )

        # If we reach here, show the selection form again with errors
        site_options = self._build_site_options()
        return self.async_show_form(
            step_id="select_site",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SITE_ID): SelectSelector(
                        SelectSelectorConfig(
                            options=site_options, mode=SelectSelectorMode.DROPDOWN
                        )
                    )
                }
            ),
            errors=errors,
        )