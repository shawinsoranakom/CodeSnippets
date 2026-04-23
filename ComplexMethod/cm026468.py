async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: MonarchMoneyConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Monarch Money sensors for config entries."""
    mm_coordinator = config_entry.runtime_data

    entity_list: list[MonarchMoneySensor | MonarchMoneyCashFlowSensor] = [
        MonarchMoneyCashFlowSensor(
            mm_coordinator,
            sensor_description,
        )
        for sensor_description in MONARCH_CASHFLOW_SENSORS
    ]
    entity_list.extend(
        MonarchMoneySensor(
            mm_coordinator,
            sensor_description,
            account,
        )
        for account in mm_coordinator.balance_accounts
        for sensor_description in MONARCH_MONEY_SENSORS
    )
    entity_list.extend(
        MonarchMoneySensor(
            mm_coordinator,
            sensor_description,
            account,
        )
        for account in mm_coordinator.accounts
        for sensor_description in MONARCH_MONEY_AGE_SENSORS
    )
    entity_list.extend(
        MonarchMoneySensor(
            mm_coordinator,
            sensor_description,
            account,
        )
        for account in mm_coordinator.value_accounts
        for sensor_description in MONARCH_MONEY_VALUE_SENSORS
    )

    async_add_entities(entity_list)