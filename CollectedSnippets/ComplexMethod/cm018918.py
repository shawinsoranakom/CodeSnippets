async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    mock_setup_entry,
    twitch_mock: AsyncMock,
    scopes: list[str],
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "twitch", context={"source": SOURCE_USER}
    )
    await _do_get_token(hass, result, hass_client_no_auth, scopes)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "channel123"
    assert "result" in result
    assert "token" in result["result"].data
    assert result["result"].data["token"]["access_token"] == "mock-access-token"
    assert result["result"].data["token"]["refresh_token"] == "mock-refresh-token"
    assert result["result"].unique_id == "123"
    assert result["options"] == {CONF_CHANNELS: ["internetofthings", "homeassistant"]}