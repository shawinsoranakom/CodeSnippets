async def test_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test diagnostic information."""
    config_entry = MockConfigEntry(domain=DOMAIN, data={}, unique_id=DOMAIN)
    config_entry.add_to_hass(hass)

    with patch.dict(os.environ, MOCK_ENVIRON):
        result = await async_setup_component(
            hass,
            "hassio",
            {"http": {"server_port": 9999, "server_host": "127.0.0.1"}, "hassio": {}},
        )
        assert result
        await hass.async_block_till_done()

    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, config_entry
    )

    assert "core" in diagnostics["coordinator_data"]
    assert "supervisor" in diagnostics["coordinator_data"]
    assert "os" in diagnostics["coordinator_data"]
    assert "host" in diagnostics["coordinator_data"]
    assert "addons" in diagnostics["addons_coordinator_data"]

    assert len(diagnostics["devices"]) == 6