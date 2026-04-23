async def test_update_check_service(
    hass: HomeAssistant,
    matter_client: MagicMock,
    check_node_update: AsyncMock,
    matter_node: MatterNode,
) -> None:
    """Test check device update through service call."""
    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "v1.0"

    await async_setup_component(hass, HA_DOMAIN, {})

    check_node_update.return_value = MatterSoftwareVersion(
        vid=65521,
        pid=32768,
        software_version=2,
        software_version_string="v2.0",
        firmware_information="",
        min_applicable_software_version=0,
        max_applicable_software_version=1,
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

    assert matter_client.check_node_update.call_count == 2

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("latest_version") == "v2.0"
    assert (
        state.attributes.get("release_url")
        == "http://home-assistant.io/non-existing-product"
    )