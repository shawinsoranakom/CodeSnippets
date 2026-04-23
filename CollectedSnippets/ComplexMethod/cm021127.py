async def test_diagnostics(
    hass: HomeAssistant,
    ufp: MockUFPFixture,
    light: Light,
    hass_client: ClientSessionGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test generating diagnostics for a config entry."""
    await init_entry(hass, ufp, [light])

    diag = await get_diagnostics_for_config_entry(hass, hass_client, ufp.entry)

    # Validate that anonymization is working - original values should not appear
    bootstrap = diag["bootstrap"]
    nvr = ufp.api.bootstrap.nvr
    assert bootstrap["nvr"]["id"] != nvr.id
    assert bootstrap["nvr"]["mac"] != nvr.mac
    assert bootstrap["nvr"]["host"] != str(nvr.host)
    assert bootstrap["lights"][0]["id"] != light.id
    assert bootstrap["lights"][0]["mac"] != light.mac
    assert bootstrap["lights"][0]["host"] != str(light.host)

    # Normalize data to remove non-deterministic values (memory addresses, random IDs)
    diag_normalized = _normalize_diagnostics(diag)

    assert diag_normalized == snapshot