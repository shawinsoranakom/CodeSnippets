async def test_intent_script(hass: HomeAssistant) -> None:
    """Test intent scripts work."""
    calls = async_mock_service(hass, "test", "service")

    await async_setup_component(
        hass,
        "intent_script",
        {
            "intent_script": {
                "HelloWorld": {
                    "description": "Intent to control a test service.",
                    "platforms": ["switch"],
                    "action": {
                        "service": "test.service",
                        "data_template": {"hello": "{{ name }}"},
                    },
                    "card": {
                        "title": "Hello {{ name }}",
                        "content": "Content for {{ name }}",
                    },
                    "speech": {"text": "Good morning {{ name }}"},
                }
            }
        },
    )

    handlers = [
        intent_handler
        for intent_handler in intent.async_get(hass)
        if intent_handler.intent_type == "HelloWorld"
    ]

    assert len(handlers) == 1
    handler = handlers[0]
    assert handler.description == "Intent to control a test service."
    assert handler.platforms == {"switch"}

    response = await intent.async_handle(
        hass, "test", "HelloWorld", {"name": {"value": "Paulus"}}
    )

    assert len(calls) == 1
    assert calls[0].data["hello"] == "Paulus"

    assert response.speech["plain"]["speech"] == "Good morning Paulus"

    assert not (response.reprompt)

    assert response.card["simple"]["title"] == "Hello Paulus"
    assert response.card["simple"]["content"] == "Content for Paulus"