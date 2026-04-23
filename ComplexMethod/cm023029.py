async def test_custom_sentences_priority(
    hass: HomeAssistant,
    hass_admin_user: MockUser,
    snapshot: SnapshotAssertion,
) -> None:
    """Test that user intents from custom_sentences have priority over builtin intents/sentences."""
    with tempfile.NamedTemporaryFile(
        mode="w+",
        encoding="utf-8",
        suffix=".yaml",
        dir=os.path.join(hass.config.config_dir, "custom_sentences", "en"),
    ) as custom_sentences_file:
        # Add a custom sentence that would match a builtin sentence.
        # Custom sentences have priority.
        yaml.dump(
            {
                "language": "en",
                "intents": {
                    "CustomIntent": {"data": [{"sentences": ["turn on the lamp"]}]}
                },
            },
            custom_sentences_file,
        )
        custom_sentences_file.flush()
        custom_sentences_file.seek(0)

        assert await async_setup_component(hass, "homeassistant", {})
        assert await async_setup_component(hass, "conversation", {})
        assert await async_setup_component(hass, "light", {})
        assert await async_setup_component(hass, "intent", {})
        assert await async_setup_component(
            hass,
            "intent_script",
            {
                "intent_script": {
                    "CustomIntent": {"speech": {"text": "custom response"}}
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