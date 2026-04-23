async def test_preview_error(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    step_id: str,
    user_input: dict,
    expected_error: str,
) -> None:
    """Test preview will error if any template errors."""
    client = await hass_ws_client(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": step_id},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == step_id
    assert result["errors"] is None
    assert result["preview"] == "template"

    await client.send_json_auto_id(
        {
            "type": "template/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": user_input,
        }
    )
    msg = await client.receive_json()

    assert msg["success"]
    assert msg["result"] is None

    # Test expected error
    msg = await client.receive_json()
    assert "error" in msg["event"]
    assert msg["event"]["error"] == expected_error

    # Test No preview is created
    with pytest.raises(TimeoutError):
        await client.receive_json(timeout=0.01)