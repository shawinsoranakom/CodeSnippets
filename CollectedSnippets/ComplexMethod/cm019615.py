async def test_update_check_with_same_numeric_version(
    hass: HomeAssistant,
    matter_client: MagicMock,
    check_node_update: AsyncMock,
    matter_node: MatterNode,
) -> None:
    """Test update detection when numeric version is unchanged."""
    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "v1.0"

    await async_setup_component(hass, HA_DOMAIN, {})

    check_node_update.return_value = MatterSoftwareVersion(
        vid=65521,
        pid=32768,
        software_version=1,
        software_version_string="1.0.0",
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

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "v1.0"
    assert state.attributes.get("latest_version") == "v1.0"