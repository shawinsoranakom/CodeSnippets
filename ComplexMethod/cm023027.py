async def test_custom_sentences_config(
    hass: HomeAssistant,
    snapshot: SnapshotAssertion,
) -> None:
    """Test custom sentences with a custom intent in config."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(
        hass,
        "conversation",
        {"conversation": {"intents": {"StealthMode": ["engage stealth mode"]}}},
    )
    assert await async_setup_component(hass, "intent", {})
    assert await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "StealthMode": {"speech": {"text": "Stealth mode engaged"}}
            }
        },
    )

    # Invoke intent via HTTP API
    result = await conversation.async_converse(
        hass, "engage stealth mode", None, Context(), None
    )

    data = result.as_dict()
    assert data == snapshot
    assert data["response"]["response_type"] == "action_done"
    assert data["response"]["speech"]["plain"]["speech"] == "Stealth mode engaged"