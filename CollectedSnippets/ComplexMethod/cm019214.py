async def test_user(hass: HomeAssistant, webhook_id, secret) -> None:
    """Test user step."""
    flow = await init_config_flow(hass)

    result = await flow.async_step_user()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user({})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OwnTracks"
    assert result["data"][CONF_WEBHOOK_ID] == WEBHOOK_ID
    assert result["data"][CONF_SECRET] == SECRET
    assert result["data"][CONF_CLOUDHOOK] == CLOUDHOOK
    assert result["description_placeholders"][CONF_WEBHOOK_URL] == WEBHOOK_URL