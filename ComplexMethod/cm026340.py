async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(info[CONF_UNIQUE_ID])
                self._abort_if_unique_id_configured()
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except NoURLAvailableError:
                errors["base"] = "missing_internal_url"
            except MissingNASwebData:
                errors["base"] = "missing_nasweb_data"
            except MissingNASwebStatus:
                errors["base"] = "missing_status"
            except AbortFlow:
                raise
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                STEP_USER_DATA_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={
                "nasweb_schema_img": '<img src="' + NASWEB_SCHEMA_IMG_URL + '"/><br>',
            },
        )