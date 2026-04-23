async def _async_check_and_create(self, step_id, user_input):
        """Validate input, proceed to create."""
        user_input[CONF_URL] = url_normalize(
            user_input[CONF_URL], default_scheme="http"
        )
        if "://" not in user_input[CONF_URL]:
            return await self._async_show_form(
                step_id=step_id, user_input=user_input, errors={CONF_URL: "invalid_url"}
            )

        # If we don't have a unique id, copy one from existing entry with same URL
        if not self.unique_id:
            for existing_entry in (
                x
                for x in self._async_current_entries()
                if x.data[CONF_URL] == user_input[CONF_URL] and x.unique_id
            ):
                await self.async_set_unique_id(existing_entry.unique_id)
                break

        session = aiohttp_client.async_get_clientsession(self.hass)
        printer = SyncThru(
            user_input[CONF_URL], session, connection_mode=ConnectionMode.API
        )
        errors = {}
        try:
            await printer.update()
            if not user_input.get(CONF_NAME):
                user_input[CONF_NAME] = DEFAULT_NAME_TEMPLATE.format(
                    printer.model() or DEFAULT_MODEL
                )
        except SyncThruAPINotSupported:
            errors[CONF_URL] = "syncthru_not_supported"
        else:
            if printer.is_unknown_state():
                errors[CONF_URL] = "unknown_state"

        if errors:
            return await self._async_show_form(
                step_id=step_id, user_input=user_input, errors=errors
            )

        return self.async_create_entry(
            title=user_input.get(CONF_NAME),
            data=user_input,
        )