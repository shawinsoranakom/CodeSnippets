async def test_tts_info(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    setup_cloud: None,
) -> None:
    """Test that we can get TTS info."""
    client = await hass_ws_client(hass)

    await client.send_json_auto_id({"type": "cloud/tts/info"})
    response = await client.receive_json()

    assert response["success"]
    assert "languages" in response["result"]
    assert all(len(lang) for lang in response["result"]["languages"])
    assert len(response["result"]["languages"]) > 300
    assert (
        len([lang for lang in response["result"]["languages"] if "||" in lang[1]]) > 100
    )
    for lang in response["result"]["languages"]:
        assert validate_language_voice(lang[:2])