async def test_config_sentences_priority(
    hass: HomeAssistant,
    hass_admin_user: MockUser,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that user intents from configuration.yaml have priority over builtin intents/sentences.

    Also test that they follow proper selection logic.
    """
    # Add a custom sentence that would match a builtin sentence.
    # Custom sentences have priority.
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})
    assert await async_setup_component(
        hass,
        "conversation",
        {
            "conversation": {
                "intents": {
                    "CustomIntent": ["turn on <name>"],
                    "WorseCustomIntent": ["turn on the lamp"],
                    "FakeCustomIntent": ["turn on <name>"],
                }
            }
        },
    )

    # Fake intent not being custom
    intents = (
        await conversation.async_get_agent(hass).async_get_or_load_intents(
            hass.config.language
        )
    ).intents.intents
    intents["FakeCustomIntent"].data[0].metadata[METADATA_CUSTOM_SENTENCE] = False

    assert await async_setup_component(hass, "light", {})
    assert await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "CustomIntent": {"speech": {"text": "custom response"}},
                "WorseCustomIntent": {"speech": {"text": "worse custom response"}},
                "FakeCustomIntent": {"speech": {"text": "fake custom response"}},
            }
        },
    )

    # Ensure that a "lamp" exists so that we can verify the custom intent
    # overrides the builtin sentence.
    hass.states.async_set("light.lamp", "off")

    result = await conversation.async_converse(
        hass,
        "turn on the lamp",
        None,
        Context(),
        language=hass.config.language,
    )
    data = result.as_dict()
    assert data["response"]["response_type"] == "action_done"
    assert data["response"]["speech"]["plain"]["speech"] == "custom response"