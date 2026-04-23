async def test_light_group_discovery_members_before_group(
    hass: HomeAssistant, mqtt_mock_entry: MqttMockHAClientGenerator
) -> None:
    """Test the discovery of a light group and linked entity IDs.

    The members are discovered first, so they are known in the entity registry.
    """
    await mqtt_mock_entry()
    # Discover light group members
    async_fire_mqtt_message(hass, GROUP_MEMBER_1_TOPIC, GROUP_DISCOVERY_MEMBER_1_CONFIG)
    async_fire_mqtt_message(hass, GROUP_MEMBER_2_TOPIC, GROUP_DISCOVERY_MEMBER_2_CONFIG)
    await hass.async_block_till_done()

    # Discover group
    async_fire_mqtt_message(hass, GROUP_TOPIC, GROUP_DISCOVERY_LIGHT_GROUP_CONFIG)

    await hass.async_block_till_done()

    assert hass.states.get("light.member1") is not None
    assert hass.states.get("light.member2") is not None
    group_state = hass.states.get("light.group")
    assert group_state is not None
    assert group_state.attributes.get("group_entities") == [
        "light.member1",
        "light.member2",
    ]

    # Now create and discover a new member
    async_fire_mqtt_message(hass, GROUP_MEMBER_3_TOPIC, GROUP_DISCOVERY_MEMBER_3_CONFIG)
    await hass.async_block_till_done()

    # Update the group discovery
    async_fire_mqtt_message(
        hass, GROUP_TOPIC, GROUP_DISCOVERY_LIGHT_GROUP_CONFIG_EXPANDED
    )

    await hass.async_block_till_done()

    assert hass.states.get("light.member1") is not None
    assert hass.states.get("light.member2") is not None
    assert hass.states.get("light.member3") is not None
    group_state = hass.states.get("light.group")
    assert group_state is not None
    assert group_state.attributes.get("group_entities") == [
        "light.member1",
        "light.member2",
        "light.member3",
    ]