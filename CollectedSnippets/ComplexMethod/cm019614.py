async def test_update_check_with_same_version_string(
    hass: HomeAssistant,
    matter_client: MagicMock,
    check_node_update: AsyncMock,
    matter_node: MatterNode,
) -> None:
    """Test update detection when versions share the same display string."""
    set_node_attribute_typed(
        matter_node,
        0,
        clusters.BasicInformation.Attributes.SoftwareVersion,
        115,
    )
    set_node_attribute_typed(
        matter_node,
        0,
        clusters.BasicInformation.Attributes.SoftwareVersionString,
        "1.1.5",
    )
    await trigger_subscription_callback(hass, matter_client)

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "1.1.5"

    await async_setup_component(hass, HA_DOMAIN, {})

    check_node_update.return_value = MatterSoftwareVersion(
        vid=65521,
        pid=32768,
        software_version=1150,
        software_version_string="1.1.5",
        firmware_information="",
        min_applicable_software_version=0,
        max_applicable_software_version=115,
        release_notes_url="http://home-assistant.io/non-existing-product",
        update_source=UpdateSource.LOCAL,
    )

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            ATTR_ENTITY_ID: "update.mock_dimmable_light_firmware",
        },
        blocking=True,
    )

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("installed_version") == "1.1.5"
    assert state.attributes.get("latest_version") == "1.1.5 (1150)"
    assert (
        state.attributes.get("release_url")
        == "http://home-assistant.io/non-existing-product"
    )

    check_node_update.return_value = None

    await hass.services.async_call(
        HA_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {
            ATTR_ENTITY_ID: "update.mock_dimmable_light_firmware",
        },
        blocking=True,
    )

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("latest_version") == "1.1.5"
    assert state.attributes.get("release_url") is None