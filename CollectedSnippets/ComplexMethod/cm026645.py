async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_ID_OR_PASSPORT])
            if self.source != SOURCE_REAUTH:
                self._abort_if_unique_id_configured()

            ituran = Ituran(
                user_input[CONF_ID_OR_PASSPORT],
                user_input[CONF_PHONE_NUMBER],
            )
            user_input[CONF_MOBILE_ID] = ituran.mobile_id
            try:
                authenticated = await ituran.is_authenticated()
                if not authenticated:
                    await ituran.request_otp()
            except IturanApiError:
                errors["base"] = "cannot_connect"
            except IturanAuthError:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if authenticated:
                    return self.async_create_entry(
                        title=f"Ituran {user_input[CONF_ID_OR_PASSPORT]}",
                        data=user_input,
                    )
                self._user_info = user_input
                return await self.async_step_otp()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )