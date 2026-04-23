async def test_update_install_failure(
    hass: HomeAssistant,
    matter_client: MagicMock,
    check_node_update: AsyncMock,
    update_node: AsyncMock,
    matter_node: MatterNode,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test update entity service call errors."""
    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_OFF
    assert state.attributes.get("installed_version") == "v1.0"

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

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done(wait_background_tasks=True)

    assert matter_client.check_node_update.call_count == 2

    state = hass.states.get("update.mock_dimmable_light_firmware")
    assert state
    assert state.state == STATE_ON
    assert state.attributes.get("latest_version") == "v2.0"
    assert (
        state.attributes.get("release_url")
        == "http://home-assistant.io/non-existing-product"
    )

    update_node.side_effect = UpdateCheckError("Error finding applicable update")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: "update.mock_dimmable_light_firmware",
                ATTR_VERSION: "v3.0",
            },
            blocking=True,
        )

    update_node.side_effect = UpdateError("Error updating node")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: "update.mock_dimmable_light_firmware",
                ATTR_VERSION: "v3.0",
            },
            blocking=True,
        )