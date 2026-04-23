def _load_json_2_encharge_enpower_data(
    mocked_data: EnvoyData, json_fixture: dict[str, Any]
) -> None:
    """Fill envoy encharge/enpower data from fixture."""
    if item := json_fixture["data"].get("encharge_inventory"):
        mocked_data.encharge_inventory = {}
        for sub_item, item_data in item.items():
            mocked_data.encharge_inventory[sub_item] = EnvoyEncharge(**item_data)
    if item := json_fixture["data"].get("enpower"):
        mocked_data.enpower = EnvoyEnpower(**item)
    if item := json_fixture["data"].get("encharge_aggregate"):
        mocked_data.encharge_aggregate = EnvoyEnchargeAggregate(**item)
    if item := json_fixture["data"].get("encharge_power"):
        mocked_data.encharge_power = {}
        for sub_item, item_data in item.items():
            mocked_data.encharge_power[sub_item] = EnvoyEnchargePower(**item_data)
    if item := json_fixture["data"].get("tariff"):
        mocked_data.tariff = EnvoyTariff(**item)
        mocked_data.tariff.storage_settings = EnvoyStorageSettings(
            **item["storage_settings"]
        )
    if item := json_fixture["data"].get("dry_contact_status"):
        mocked_data.dry_contact_status = {}
        for sub_item, item_data in item.items():
            mocked_data.dry_contact_status[sub_item] = EnvoyDryContactStatus(
                **item_data
            )
    if item := json_fixture["data"].get("dry_contact_settings"):
        mocked_data.dry_contact_settings = {}
        for sub_item, item_data in item.items():
            mocked_data.dry_contact_settings[sub_item] = EnvoyDryContactSettings(
                **item_data
            )
    if item := json_fixture["data"].get("battery_aggregate"):
        mocked_data.battery_aggregate = EnvoyBatteryAggregate(**item)
    if item := json_fixture["data"].get("collar"):
        mocked_data.collar = EnvoyCollar(**item)
    if item := json_fixture["data"].get("c6cc"):
        mocked_data.c6cc = EnvoyC6CC(**item)