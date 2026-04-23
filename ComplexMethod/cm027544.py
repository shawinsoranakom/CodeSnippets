async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: CoinbaseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Coinbase sensor platform."""
    instance = config_entry.runtime_data

    entities: list[SensorEntity] = []

    provided_currencies: list[str] = [
        account[API_ACCOUNT_CURRENCY]
        for account in instance.accounts
        if not account[ACCOUNT_IS_VAULT]
    ]

    desired_currencies: list[str] = []

    if CONF_CURRENCIES in config_entry.options:
        desired_currencies = config_entry.options[CONF_CURRENCIES]

    exchange_base_currency: str = instance.exchange_rates[API_ACCOUNT_CURRENCY]

    exchange_precision: int = config_entry.options.get(
        CONF_EXCHANGE_PRECISION, CONF_EXCHANGE_PRECISION_DEFAULT
    )

    # Remove orphaned entities
    registry = er.async_get(hass)
    existing_entities = er.async_entries_for_config_entry(
        registry, config_entry.entry_id
    )
    for entity in existing_entities:
        currency = entity.unique_id.split("-")[-1]
        if (
            "xe" in entity.unique_id
            and currency not in config_entry.options.get(CONF_EXCHANGE_RATES, [])
        ) or (
            "wallet" in entity.unique_id
            and currency not in config_entry.options.get(CONF_CURRENCIES, [])
        ):
            registry.async_remove(entity.entity_id)

    for currency in desired_currencies:
        _LOGGER.debug(
            "Attempting to set up %s account sensor",
            currency,
        )
        if currency not in provided_currencies:
            _LOGGER.warning(
                (
                    "The currency %s is no longer provided by your account, please"
                    " check your settings in Coinbase's developer tools"
                ),
                currency,
            )
            continue
        entities.append(AccountSensor(instance, currency))

    if CONF_EXCHANGE_RATES in config_entry.options:
        for rate in config_entry.options[CONF_EXCHANGE_RATES]:
            _LOGGER.debug(
                "Attempting to set up %s exchange rate sensor",
                rate,
            )
            entities.append(
                ExchangeRateSensor(
                    instance, rate, exchange_base_currency, exchange_precision
                )
            )

    async_add_entities(entities)