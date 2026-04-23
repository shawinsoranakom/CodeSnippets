def _load_json_2_production_data(
    mocked_data: EnvoyData, json_fixture: dict[str, Any]
) -> None:
    """Fill envoy production data from fixture."""
    if item := json_fixture["data"].get("system_consumption"):
        mocked_data.system_consumption = EnvoySystemConsumption(**item)
    if item := json_fixture["data"].get("system_net_consumption"):
        mocked_data.system_net_consumption = EnvoySystemConsumption(**item)
    if item := json_fixture["data"].get("system_production"):
        mocked_data.system_production = EnvoySystemProduction(**item)
    if item := json_fixture["data"].get("system_consumption_phases"):
        mocked_data.system_consumption_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.system_consumption_phases[sub_item] = EnvoySystemConsumption(
                **item_data
            )
    if item := json_fixture["data"].get("system_net_consumption_phases"):
        mocked_data.system_net_consumption_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.system_net_consumption_phases[sub_item] = (
                EnvoySystemConsumption(**item_data)
            )
    if item := json_fixture["data"].get("system_production_phases"):
        mocked_data.system_production_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.system_production_phases[sub_item] = EnvoySystemProduction(
                **item_data
            )
    if item := json_fixture["data"].get("acb_power"):
        mocked_data.acb_power = EnvoyACBPower(**item)