async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        errors = {}

        if user_input:
            data: dict[str, Any] = {}
            if self.source == SOURCE_REAUTH:
                data = dict(self._get_reauth_entry().data)
            data = {
                **data,
                **user_input,
            }

            self._client = create_client_session(self.hass)
            self._installation_key = generate_installation_key(
                str(uuid.uuid4()).lower()
            )
            cloud_client = LaMarzoccoCloudClient(
                username=data[CONF_USERNAME],
                password=data[CONF_PASSWORD],
                client=self._client,
                installation_key=self._installation_key,
            )
            try:
                await cloud_client.async_register_client()
                things = await cloud_client.list_things()
            except AuthFail:
                _LOGGER.debug("Server rejected login credentials")
                errors["base"] = "invalid_auth"
            except RequestNotSuccessful as exc:
                _LOGGER.error("Error connecting to server: %s", exc)
                errors["base"] = "cannot_connect"
            else:
                self._things = {thing.serial_number: thing for thing in things}
                if not self._things:
                    errors["base"] = "no_machines"

            if not errors:
                self._config = data
                if self.source == SOURCE_REAUTH:
                    return self.async_update_reload_and_abort(
                        self._get_reauth_entry(), data_updates=data
                    )
                if self._discovered:
                    if self._discovered[CONF_MACHINE] not in self._things:
                        errors["base"] = "machine_not_found"
                    else:
                        # store discovered connection address
                        if CONF_MAC in self._discovered:
                            self._config[CONF_MAC] = self._discovered[CONF_MAC]
                        if CONF_ADDRESS in self._discovered:
                            self._config[CONF_ADDRESS] = self._discovered[CONF_ADDRESS]

                        return await self.async_step_machine_selection(
                            user_input={CONF_MACHINE: self._discovered[CONF_MACHINE]}
                        )
            if not errors:
                return await self.async_step_machine_selection()

        placeholders: dict[str, str] | None = None
        if self._discovered:
            self.context["title_placeholders"] = placeholders = {
                CONF_NAME: self._discovered[CONF_MACHINE]
            }

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.EMAIL, autocomplete="username"
                        )
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(
                            type=TextSelectorType.PASSWORD,
                            autocomplete="current-password",
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders=placeholders,
        )