async def _async_validate(
        self, error_step_id: str, error_schema: vol.Schema
    ) -> ConfigFlowResult:
        """Validate input credentials and proceed accordingly."""
        errors = {}
        session = aiohttp_client.async_get_clientsession(self.hass)

        if TYPE_CHECKING:
            assert self._password
            assert self._username

        try:
            await async_get_client(self._username, self._password, session=session)
        except InvalidCredentialsError:
            errors["base"] = "invalid_auth"
        except RidwellError as err:
            LOGGER.error("Unknown Ridwell error: %s", err)
            errors["base"] = "unknown"

        if errors:
            return self.async_show_form(
                step_id=error_step_id,
                data_schema=error_schema,
                errors=errors,
                description_placeholders={CONF_USERNAME: self._username},
            )

        if existing_entry := await self.async_set_unique_id(self._username):
            self.hass.config_entries.async_update_entry(
                existing_entry,
                data={**existing_entry.data, CONF_PASSWORD: self._password},
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(existing_entry.entry_id)
            )
            return self.async_abort(reason="reauth_successful")

        return self.async_create_entry(
            title=self._username,
            data={CONF_USERNAME: self._username, CONF_PASSWORD: self._password},
        )