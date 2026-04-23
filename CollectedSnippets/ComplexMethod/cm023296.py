async def test_update_entity_full_restore_data_update_available(
    hass: HomeAssistant,
    client: MagicMock,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    hass_ws_client: WebSocketGenerator,
    entity_id: str,
    installed_version: str,
    install_result: dict[str, Any],
    install_command_params: dict[str, Any],
) -> None:
    """Test update entity with full restore data (update available) restores state."""
    mock_restore_cache_with_extra_data(
        hass,
        [
            (
                State(
                    entity_id,
                    STATE_OFF,
                    {
                        ATTR_INSTALLED_VERSION: installed_version,
                        ATTR_LATEST_VERSION: "11.2.4",
                        ATTR_SKIPPED_VERSION: None,
                    },
                ),
                {"latest_version_firmware": LATEST_VERSION_FIRMWARE},
            )
        ],
    )
    entry = MockConfigEntry(domain="zwave_js", data={"url": "ws://test.org"})
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_SKIPPED_VERSION] is None
    assert state.attributes[ATTR_LATEST_VERSION] == "11.2.4"

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"result": install_result}

    # Test successful install call without a version
    install_task = hass.async_create_task(
        hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: entity_id,
            },
            blocking=True,
        )
    )

    # Sleep so that task starts
    await asyncio.sleep(0.05)

    state = hass.states.get(entity_id)
    assert state
    attrs = state.attributes
    assert attrs[ATTR_IN_PROGRESS] is True
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None

    assert client.async_send_command.call_count == 1
    assert client.async_send_command.call_args[0][0] == {
        **install_command_params,
        "updateInfo": {
            "version": "11.2.4",
            "changelog": "blah 2",
            "channel": "stable",
            "files": [
                {"target": 0, "url": "https://example2.com", "integrity": "sha2"}
            ],
            "downgrade": True,
            "normalizedVersion": "11.2.4",
            "device": {
                "manufacturerId": 1,
                "productType": 2,
                "productId": 3,
                "firmwareVersion": "0.4.4",
                "rfRegion": 1,
            },
        },
    }

    install_task.cancel()