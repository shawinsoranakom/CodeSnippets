async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            url = URL(user_input[CONF_URL])
            username = user_input[SECTION_AUTH].get(CONF_USERNAME)
            self._async_abort_entries_match(
                {
                    CONF_URL: url.human_repr(),
                    CONF_USERNAME: username,
                }
            )
            session = async_get_clientsession(self.hass, user_input[CONF_VERIFY_SSL])
            if username:
                ntfy = Ntfy(
                    user_input[CONF_URL],
                    session,
                    username,
                    user_input[SECTION_AUTH].get(CONF_PASSWORD, ""),
                )
            else:
                ntfy = Ntfy(user_input[CONF_URL], session)

            try:
                account = await ntfy.account()
                token = (
                    (await ntfy.generate_token("Home Assistant")).token
                    if account.username != "*"
                    else None
                )
            except NtfyUnauthorizedAuthenticationError:
                errors["base"] = "invalid_auth"
            except NtfyHTTPError as e:
                _LOGGER.debug("Error %s: %s [%s]", e.code, e.error, e.link)
                errors["base"] = "cannot_connect"
            except NtfyException:
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                if TYPE_CHECKING:
                    assert url.host
                return self.async_create_entry(
                    title=url.host,
                    data={
                        CONF_URL: url.human_repr(),
                        CONF_USERNAME: username,
                        CONF_TOKEN: token,
                        CONF_VERIFY_SSL: user_input[CONF_VERIFY_SSL],
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=STEP_USER_DATA_SCHEMA, suggested_values=user_input
            ),
            errors=errors,
        )