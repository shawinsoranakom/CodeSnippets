async def help_test_discovery_update(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    domain: str,
    discovery_config1: DiscoveryInfoType,
    discovery_config2: DiscoveryInfoType,
    state_data1: _StateDataType | None = None,
    state_data2: _StateDataType | None = None,
) -> None:
    """Test update of discovered component.

    This is a test helper for the MqttDiscoveryUpdate mixin.
    """
    await mqtt_mock_entry()
    # Add some future configuration to the configurations
    config1 = copy.deepcopy(discovery_config1)
    config1["some_future_option_1"] = "future_option_1"
    config2 = copy.deepcopy(discovery_config2)
    config2["some_future_option_2"] = "future_option_2"
    discovery_data1 = json.dumps(config1)
    discovery_data2 = json.dumps(config2)

    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", discovery_data1)
    await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.beer")
    assert state is not None
    assert state.name == "Beer"

    if state_data1:
        for mqtt_messages, expected_state, attributes in state_data1:
            for topic, data in mqtt_messages:
                async_fire_mqtt_message(hass, topic, data)
            state = hass.states.get(f"{domain}.beer")
            assert state is not None
            if expected_state:
                assert state.state == expected_state
            if attributes:
                for attr, value in attributes:
                    assert state.attributes.get(attr) == value

    async_fire_mqtt_message(hass, f"homeassistant/{domain}/bla/config", discovery_data2)
    await hass.async_block_till_done()

    state = hass.states.get(f"{domain}.beer")
    assert state is not None
    assert state.name == "Milk"

    if state_data2:
        for mqtt_messages, expected_state, attributes in state_data2:
            for topic, data in mqtt_messages:
                async_fire_mqtt_message(hass, topic, data)
            state = hass.states.get(f"{domain}.beer")
            assert state is not None
            if expected_state:
                assert state.state == expected_state
            if attributes:
                for attr, value in attributes:
                    assert state.attributes.get(attr) == value

    state = hass.states.get(f"{domain}.milk")
    assert state is None