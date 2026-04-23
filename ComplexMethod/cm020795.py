async def test_flow_reauth(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test reauth flow."""
    with patch("homeassistant.components.tautulli.PLATFORMS", []):
        entry = await setup_integration(hass, aioclient_mock)
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

    new_conf = {CONF_API_KEY: "efgh"}
    CONF_DATA[CONF_API_KEY] = "efgh"
    with (
        patch_config_flow_tautulli(AsyncMock()),
        patch("homeassistant.components.tautulli.async_setup_entry") as mock_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=new_conf,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert entry.data == CONF_DATA
    assert len(mock_entry.mock_calls) == 1