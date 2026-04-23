async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        currencies = await self.async_get_currencies()

        if user_input is None:
            existing_data: Mapping[str, Any] = {}
            if self.source == SOURCE_REAUTH:
                existing_data = self._get_reauth_entry().data
            return self.async_show_form(
                step_id="user",
                data_schema=get_data_schema(currencies, existing_data),
                description_placeholders={
                    "signup": "https://openexchangerates.org/signup"
                },
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except OpenExchangeRatesAuthError:
            errors["base"] = "invalid_auth"
        except OpenExchangeRatesClientError:
            errors["base"] = "cannot_connect"
        except TimeoutError:
            errors["base"] = "timeout_connect"
        except Exception:  # noqa: BLE001
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            self._async_abort_entries_match(
                {
                    CONF_API_KEY: user_input[CONF_API_KEY],
                    CONF_BASE: user_input[CONF_BASE],
                }
            )

            if self.source == SOURCE_REAUTH:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates=user_input
                )

            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=get_data_schema(currencies, user_input),
            description_placeholders={"signup": "https://openexchangerates.org/signup"},
            errors=errors,
        )