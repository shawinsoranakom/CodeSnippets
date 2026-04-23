async def async_step_reauth_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle reauthentication confirmation."""
        errors: dict[str, str] = {}

        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "account_name": self.reauth_entry.title,
                    "developer_url": "https://www.coinbase.com/developer-platform",
                },
                errors=errors,
            )

        try:
            await validate_api(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidKey:
            errors["base"] = "invalid_auth_key"
        except InvalidSecret:
            errors["base"] = "invalid_auth_secret"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_update_reload_and_abort(
                self.reauth_entry,
                data_updates=user_input,
                reason="reauth_successful",
            )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=STEP_USER_DATA_SCHEMA,
            description_placeholders={
                "account_name": self.reauth_entry.title,
                "developer_url": "https://www.coinbase.com/developer-platform",
            },
            errors=errors,
        )