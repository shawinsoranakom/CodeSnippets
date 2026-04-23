async def test_switch(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_vodafone_station_router: AsyncMock,
    mock_config_entry: MockConfigEntry,
    wifi_key: str,
    wifi_name: str,
    wifi_state: str,
) -> None:
    """Test switch."""

    mock_vodafone_station_router.get_wifi_data.return_value = {
        WIFI_DATA: {
            f"{wifi_key}": {
                "on": 1 if wifi_state == "on" else 0,
                "ssid": f"{wifi_name}",
            }
        }
    }

    await setup_integration(hass, mock_config_entry)

    entity_id = f"switch.vodafone_station_{TEST_SERIAL_NUMBER}_{slugify(wifi_name)}"
    assert (state := hass.states.get(entity_id))
    assert state.state == wifi_state

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert mock_vodafone_station_router.set_wifi_status.call_count == 1

    mock_vodafone_station_router.get_wifi_data.return_value = {
        WIFI_DATA: {
            f"{wifi_key}": {
                "on": 0 if wifi_state == "on" else 1,
                "ssid": f"{wifi_name}",
            }
        }
    }

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert (state := hass.states.get(entity_id))
    assert state.state == ("off" if wifi_state == "on" else "on")