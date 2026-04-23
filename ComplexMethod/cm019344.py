def _load_json_2_meter_data(
    mocked_data: EnvoyData, json_fixture: dict[str, Any]
) -> None:
    """Fill envoy meter data from fixture."""
    if meters := json_fixture["data"].get("ctmeters"):
        mocked_data.ctmeters = {}
        [
            mocked_data.ctmeters.update({meter: EnvoyMeterData(**meter_data)})
            for meter, meter_data in meters.items()
        ]
    if meters := json_fixture["data"].get("ctmeters_phases"):
        mocked_data.ctmeters_phases = {}
        for meter, meter_data in meters.items():
            meter_phase_data: dict[str, EnvoyMeterData] = {}
            [
                meter_phase_data.update({phase: EnvoyMeterData(**phase_data)})
                for phase, phase_data in meter_data.items()
            ]
            mocked_data.ctmeters_phases.update({meter: meter_phase_data})

    if item := json_fixture["data"].get("ctmeter_production"):
        mocked_data.ctmeter_production = EnvoyMeterData(**item)
    if item := json_fixture["data"].get("ctmeter_consumption"):
        mocked_data.ctmeter_consumption = EnvoyMeterData(**item)
    if item := json_fixture["data"].get("ctmeter_storage"):
        mocked_data.ctmeter_storage = EnvoyMeterData(**item)
    if item := json_fixture["data"].get("ctmeter_production_phases"):
        mocked_data.ctmeter_production_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.ctmeter_production_phases[sub_item] = EnvoyMeterData(
                **item_data
            )
    if item := json_fixture["data"].get("ctmeter_consumption_phases"):
        mocked_data.ctmeter_consumption_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.ctmeter_consumption_phases[sub_item] = EnvoyMeterData(
                **item_data
            )
    if item := json_fixture["data"].get("ctmeter_storage_phases"):
        mocked_data.ctmeter_storage_phases = {}
        for sub_item, item_data in item.items():
            mocked_data.ctmeter_storage_phases[sub_item] = EnvoyMeterData(**item_data)