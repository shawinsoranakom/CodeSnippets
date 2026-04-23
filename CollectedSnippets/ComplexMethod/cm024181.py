async def test_discovery_expansion(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test expansion of abbreviated discovery payload."""
    await mqtt_mock_entry()
    data = (
        '{ "~": "some/base/topic",'
        '  "name": "DiscoveryExpansionTest1",'
        '  "stat_t": "test_topic/~",'
        '  "cmd_t": "~/test_topic",'
        '  "availability": ['
        "    {"
        '      "topic":"~/avail_item1",'
        '      "payload_available": "available",'
        '      "payload_not_available": "not_available"'
        "    },"
        "    {"
        '      "t":"avail_item2/~",'
        '      "pl_avail": "available",'
        '      "pl_not_avail": "not_available"'
        "    }"
        "  ],"
        '  "dev":{'
        '    "ids":["5706DF"],'
        '    "name":"DiscoveryExpansionTest1 Device",'
        '    "mdl":"Generic",'
        '    "hw":"rev1",'
        '    "sw":"1.2.3.4",'
        '    "mf":"None",'
        '    "sa":"default_area"'
        "  }"
        "}"
    )

    async_fire_mqtt_message(hass, "homeassistant/switch/bla/config", data)
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE

    async_fire_mqtt_message(hass, "avail_item2/some/base/topic", "available")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state is not None
    assert state.name == "DiscoveryExpansionTest1"
    assert ("switch", "bla") in hass.data["mqtt"].discovery_already_discovered
    assert state.state == STATE_UNKNOWN

    async_fire_mqtt_message(hass, "test_topic/some/base/topic", "ON")

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_ON

    async_fire_mqtt_message(hass, "some/base/topic/avail_item1", "not_available")
    await hass.async_block_till_done()

    state = hass.states.get("switch.DiscoveryExpansionTest1")
    assert state and state.state == STATE_UNAVAILABLE