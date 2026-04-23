async def test_preview_feature_urls_present(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Test that preview features include feedback and report URLs."""
    hass.config.components.add("kitchen_sink")
    assert await async_setup(hass, {})
    await hass.async_block_till_done()

    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "labs/list"})
    msg = await client.receive_json()

    assert msg["success"]
    feature = msg["result"]["features"][0]
    assert "feedback_url" in feature
    assert "learn_more_url" in feature
    assert "report_issue_url" in feature
    assert feature["feedback_url"] is not None
    assert feature["learn_more_url"] is not None
    assert feature["report_issue_url"] is not None