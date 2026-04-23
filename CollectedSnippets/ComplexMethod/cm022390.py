async def test_disable_entry(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that we can disable entry."""
    assert await async_setup_component(hass, "config", {})
    ws_client = await hass_ws_client(hass)

    entry = MockConfigEntry(domain="test", state=core_ce.ConfigEntryState.LOADED)
    entry.add_to_hass(hass)
    assert entry.disabled_by is None
    hass.config.components.add("test")

    # Disable
    await ws_client.send_json(
        {
            "id": 5,
            "type": "config_entries/disable",
            "entry_id": entry.entry_id,
            "disabled_by": core_ce.ConfigEntryDisabler.USER,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] == {"require_restart": True}
    assert entry.disabled_by is core_ce.ConfigEntryDisabler.USER
    assert entry.state is core_ce.ConfigEntryState.FAILED_UNLOAD

    # Enable
    await ws_client.send_json(
        {
            "id": 6,
            "type": "config_entries/disable",
            "entry_id": entry.entry_id,
            "disabled_by": None,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] == {"require_restart": True}
    assert entry.disabled_by is None
    assert entry.state == core_ce.ConfigEntryState.FAILED_UNLOAD

    # Enable again -> no op
    await ws_client.send_json(
        {
            "id": 7,
            "type": "config_entries/disable",
            "entry_id": entry.entry_id,
            "disabled_by": None,
        }
    )
    response = await ws_client.receive_json()

    assert response["success"]
    assert response["result"] == {"require_restart": False}
    assert entry.disabled_by is None
    assert entry.state == core_ce.ConfigEntryState.FAILED_UNLOAD