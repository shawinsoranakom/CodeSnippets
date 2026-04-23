async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""

        errors = {}
        default_currencies = self.config_entry.options.get(CONF_CURRENCIES, [])
        default_exchange_rates = self.config_entry.options.get(CONF_EXCHANGE_RATES, [])
        default_exchange_base = self.config_entry.options.get(CONF_EXCHANGE_BASE, "USD")
        default_exchange_precision = self.config_entry.options.get(
            CONF_EXCHANGE_PRECISION, CONF_EXCHANGE_PRECISION_DEFAULT
        )

        if user_input is not None:
            # Pass back user selected options, even if bad
            if CONF_CURRENCIES in user_input:
                default_currencies = user_input[CONF_CURRENCIES]

            if CONF_EXCHANGE_RATES in user_input:
                default_exchange_rates = user_input[CONF_EXCHANGE_RATES]

            if CONF_EXCHANGE_RATES in user_input:
                default_exchange_base = user_input[CONF_EXCHANGE_BASE]

            if CONF_EXCHANGE_PRECISION in user_input:
                default_exchange_precision = user_input[CONF_EXCHANGE_PRECISION]

            try:
                await validate_options(self.hass, self.config_entry, user_input)
            except CurrencyUnavailable:
                errors["base"] = "currency_unavailable"
            except ExchangeRateUnavailable:
                errors["base"] = "exchange_rate_unavailable"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_CURRENCIES,
                        default=default_currencies,
                    ): cv.multi_select(WALLETS),
                    vol.Optional(
                        CONF_EXCHANGE_RATES,
                        default=default_exchange_rates,
                    ): cv.multi_select(RATES),
                    vol.Optional(
                        CONF_EXCHANGE_BASE,
                        default=default_exchange_base,
                    ): vol.In(WALLETS),
                    vol.Optional(
                        CONF_EXCHANGE_PRECISION, default=default_exchange_precision
                    ): int,
                }
            ),
            errors=errors,
        )