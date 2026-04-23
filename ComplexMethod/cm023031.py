async def test_entities_filtered_by_input(hass: HomeAssistant) -> None:
    """Test that entities are filtered by the input text before intent matching."""
    agent = async_get_agent(hass)

    # Only the switch is exposed
    hass.states.async_set("light.test_light", "off")
    hass.states.async_set(
        "light.test_light_2", "off", attributes={ATTR_FRIENDLY_NAME: "test light"}
    )
    hass.states.async_set("cover.garage_door", "closed")
    hass.states.async_set("switch.test_switch", "off")
    expose_entity(hass, "light.test_light", False)
    expose_entity(hass, "light.test_light_2", False)
    expose_entity(hass, "cover.garage_door", False)
    expose_entity(hass, "switch.test_switch", True)
    await hass.async_block_till_done()

    # test switch is exposed
    user_input = ConversationInput(
        text="turn on test switch",
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=None,
    ) as recognize_best:
        await agent.async_recognize_intent(user_input)

        # (1) exposed, (2) all entities
        assert len(recognize_best.call_args_list) == 2

        # Only the test light should have been considered because its name shows
        # up in the input text.
        slot_lists = recognize_best.call_args_list[0].kwargs["slot_lists"]
        name_list = slot_lists["name"]
        assert len(name_list.values) == 1
        assert name_list.values[0].text_in.text == "test switch"

    # test light is not exposed
    user_input = ConversationInput(
        text="turn on Test Light",  # different casing for name
        context=Context(),
        conversation_id=None,
        device_id=None,
        satellite_id=None,
        language=hass.config.language,
        agent_id=None,
    )

    with patch(
        "homeassistant.components.conversation.default_agent.recognize_best",
        return_value=None,
    ) as recognize_best:
        await agent.async_recognize_intent(user_input)

        # (1) exposed, (2) all entities
        assert len(recognize_best.call_args_list) == 2

        # Both test lights should have been considered because their name shows
        # up in the input text.
        slot_lists = recognize_best.call_args_list[1].kwargs["slot_lists"]
        name_list = slot_lists["name"]
        assert len(name_list.values) == 2
        assert name_list.values[0].text_in.text == "test light"
        assert name_list.values[1].text_in.text == "test light"