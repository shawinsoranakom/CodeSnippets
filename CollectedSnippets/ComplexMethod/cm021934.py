async def test_entry_diagnostics_with_homes(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    config_entry: MockConfigEntry,
    mock_tibber_setup: MagicMock,
) -> None:
    """Test config entry diagnostics with homes."""
    tibber_mock = mock_tibber_setup
    tibber_mock.get_homes.side_effect = mock_get_homes

    result = await get_diagnostics_for_config_entry(hass, hass_client, config_entry)

    assert isinstance(result, dict)
    assert "homes" in result
    assert "devices" in result

    homes = result["homes"]
    assert isinstance(homes, list)
    assert len(homes) == 1

    home = homes[0]
    assert "last_data_timestamp" in home
    assert "has_active_subscription" in home
    assert "has_real_time_consumption" in home
    assert "last_cons_data_timestamp" in home
    assert "country" in home
    assert home["has_active_subscription"] is True
    assert home["has_real_time_consumption"] is False
    assert home["country"] == "NO"