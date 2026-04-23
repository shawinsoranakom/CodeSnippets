async def test_light_group_discovery_group_before_members(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test the discovery of a light group and linked entity IDs.

    The group is discovered first, so the group members are
    not (all) known yet in the entity registry.
    The entity property should be updated as soon as member entities
    are discovered, updated or removed.
    """
    await mqtt_mock_entry()

    # Discover group
    async_fire_mqtt_message(hass, GROUP_TOPIC, GROUP_DISCOVERY_LIGHT_GROUP_CONFIG)
    await hass.async_block_till_done()

    # Discover light group members
    async_fire_mqtt_message(hass, GROUP_MEMBER_1_TOPIC, GROUP_DISCOVERY_MEMBER_1_CONFIG)
    async_fire_mqtt_message(hass, GROUP_MEMBER_2_TOPIC, GROUP_DISCOVERY_MEMBER_2_CONFIG)

    await hass.async_block_till_done()

    assert hass.states.get("light.member1") is not None
    assert hass.states.get("light.member2") is not None

    group_state = hass.states.get("light.group")
    assert group_state is not None
    assert group_state.attributes.get("group_entities") == [
        "light.member1",
        "light.member2",
    ]

    # Remove member 1
    async_fire_mqtt_message(hass, GROUP_MEMBER_1_TOPIC, "")

    await hass.async_block_till_done()

    assert hass.states.get("light.member1") is None
    assert hass.states.get("light.member2") is not None

    group_state = hass.states.get("light.group")
    assert group_state is not None
    assert group_state.attributes.get("group_entities") == ["light.member2"]

    # Rename member 2
    entity_registry.async_update_entity(
        "light.member2", new_entity_id="light.member2_updated"
    )

    await hass.async_block_till_done()

    group_state = hass.states.get("light.group")
    assert group_state is not None
    assert group_state.attributes.get("group_entities") == ["light.member2_updated"]