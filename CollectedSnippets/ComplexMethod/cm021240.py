async def test_entry_diagnostics(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    init_integration: MockConfigEntry,
    snapshot: SnapshotAssertion,
) -> None:
    """Test config entry diagnostics payload and redaction."""
    connected_clients_data = json.loads(
        await async_load_fixture(hass, "connected-clients.json", DOMAIN)
    )

    controller = init_integration.runtime_data
    controller.clients_coordinator.data = {
        client["mac"]: OmadaWirelessClient(client)
        for client in connected_clients_data[:2]
    }

    result = await get_diagnostics_for_config_entry(hass, hass_client, init_integration)

    assert {"entry", "runtime"} <= result.keys()
    assert {"devices", "clients", "gateway"} <= result["runtime"].keys()

    entry_data = result["entry"]["data"]
    assert entry_data["host"] == "**REDACTED**"
    assert entry_data["username"] == "**REDACTED**"
    assert entry_data["password"] == "**REDACTED**"

    # Runtime sections should use pseudonymized MAC keys rather than raw values.
    assert "AA-BB-CC-DD-EE-FF" not in result["runtime"]["devices"]
    assert "16-32-50-ED-FB-15" not in result["runtime"]["clients"]
    assert len(result["runtime"]["clients"]) == 2

    payload = json.dumps(result)
    assert "AA-BB-CC-DD-EE-FF" not in payload
    assert "16-32-50-ED-FB-15" not in payload
    assert "2E-DC-E1-C4-37-D3" not in payload
    assert "192.168.1.177" not in payload
    assert "OFFICE_SSID" not in payload
    assert "140.100.128.10" not in payload

    assert result == snapshot(exclude=props("entry_id", "created_at", "modified_at"))