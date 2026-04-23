async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """First step: ask for API token and validate it."""
        errors: dict[str, str] = {}
        if user_input is not None:
            api_token: str = user_input[CONF_API_TOKEN]
            try:
                sites = await self._async_validate_token_and_fetch_sites(api_token)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if not sites:
                    return self.async_show_form(
                        step_id="user",
                        data_schema=STEP_USER_DATA_SCHEMA,
                        errors={"base": "no_sites"},
                    )
                self._api_token = api_token
                # Sort sites by name then id for stable order
                self._sites = sorted(sites, key=lambda s: (s.name or "", s.id))
                if len(self._sites) == 1:
                    # Only one site available, skip site selection step
                    site = self._sites[0]
                    await self.async_set_unique_id(
                        str(site.id), raise_on_progress=False
                    )
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"VRM for {site.name}",
                        data={CONF_API_TOKEN: self._api_token, CONF_SITE_ID: site.id},
                    )
                return await self.async_step_select_site()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )