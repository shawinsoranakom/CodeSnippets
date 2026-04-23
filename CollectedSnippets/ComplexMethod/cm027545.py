async def validate_options(
    hass: HomeAssistant, config_entry: CoinbaseConfigEntry, options
):
    """Validate the requested resources are provided by API."""

    client = config_entry.runtime_data.client

    accounts = await hass.async_add_executor_job(get_accounts, client)

    accounts_currencies = [
        account[API_ACCOUNT_CURRENCY]
        for account in accounts
        if not account[ACCOUNT_IS_VAULT]
    ]

    resp = await hass.async_add_executor_job(client.get, "/v2/exchange-rates")
    available_rates = resp[API_DATA]

    if CONF_CURRENCIES in options:
        for currency in options[CONF_CURRENCIES]:
            if currency not in accounts_currencies:
                raise CurrencyUnavailable

    if CONF_EXCHANGE_RATES in options:
        for rate in options[CONF_EXCHANGE_RATES]:
            if rate not in available_rates[API_RATES]:
                raise ExchangeRateUnavailable

    return True