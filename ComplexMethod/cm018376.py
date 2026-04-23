async def test_reauth_flow(
    hass: HomeAssistant,
    requests_mock: requests_mock.Mocker,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test handling authentication errors and reauth flow."""
    mock_json = json.loads(await async_load_fixture(hass, "metoffice.json", DOMAIN))
    wavertree_daily = json.dumps(mock_json["wavertree_daily"])
    wavertree_hourly = json.dumps(mock_json["wavertree_hourly"])
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=wavertree_hourly,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data=METOFFICE_CONFIG_WAVERTREE,
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert len(device_registry.devices) == 1

    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text="",
        status_code=401,
    )
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text="",
        status_code=401,
    )

    await entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"],
        {CONF_API_KEY: TEST_API_KEY},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}

    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/daily",
        text=wavertree_daily,
    )
    requests_mock.get(
        "https://data.hub.api.metoffice.gov.uk/sitespecific/v0/point/hourly",
        text=wavertree_hourly,
    )

    result = await hass.config_entries.flow.async_configure(
        flows[0]["flow_id"],
        {CONF_API_KEY: TEST_API_KEY},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"