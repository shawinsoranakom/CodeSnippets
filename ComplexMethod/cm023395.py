async def test_full_flow_implementation(hass: HomeAssistant, mock_tellduslive) -> None:
    """Test registering an implementation and finishing flow works."""
    flow = init_config_flow(hass)
    flow.context = {"source": SOURCE_DISCOVERY}
    result = await flow.async_step_discovery(["localhost", "tellstick"])
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert len(flow._hosts) == 2

    result = await flow.async_step_user()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await flow.async_step_user({"host": "localhost"})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["description_placeholders"] == {
        "auth_url": "https://example.com",
        "app_name": APPLICATION_NAME,
    }

    result = await flow.async_step_auth("")
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "localhost"
    assert result["data"]["host"] == "localhost"
    assert result["data"]["scan_interval"] == 60
    assert result["data"]["session"] == {"token": "token", "host": "localhost"}