async def test_assist_api(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    device_registry: dr.DeviceRegistry,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test Assist API."""
    assert await async_setup_component(hass, "homeassistant", {})

    entity_registry.async_get_or_create(
        "light",
        "kitchen",
        "mock-id-kitchen",
        original_name="Kitchen",
        suggested_object_id="kitchen",
    ).write_unavailable_state(hass)

    test_context = Context()
    llm_context = llm.LLMContext(
        platform="test_platform",
        context=test_context,
        language="*",
        assistant="conversation",
        device_id=None,
    )
    schema = {
        vol.Optional("area"): cv.string,
        vol.Optional("floor"): cv.string,
        vol.Optional("preferred_area_id"): cv.string,
        vol.Optional("preferred_floor_id"): cv.string,
    }

    class MyIntentHandler(intent.IntentHandler):
        intent_type = "test_intent"
        slot_schema = schema
        platforms = set()  # Match none

    intent_handler = MyIntentHandler()

    intent.async_register(hass, intent_handler)

    assert len(llm.async_get_apis(hass)) == 1
    api = await llm.async_get_api(hass, "assist", llm_context)
    assert [tool.name for tool in api.tools] == ["GetDateTime", "GetLiveContext"]

    # Match all
    intent_handler.platforms = None

    api = await llm.async_get_api(hass, "assist", llm_context)
    assert [tool.name for tool in api.tools] == [
        "test_intent",
        "GetDateTime",
        "GetLiveContext",
    ]

    # Match specific domain
    intent_handler.platforms = {"light"}

    api = await llm.async_get_api(hass, "assist", llm_context)
    assert len(api.tools) == 3
    tool = api.tools[0]
    assert tool.name == "test_intent"
    assert tool.description == "Execute Home Assistant test_intent intent"
    assert tool.parameters == vol.Schema(
        {
            vol.Optional("area"): cv.string,
            vol.Optional("floor"): cv.string,
            # No preferred_area_id, preferred_floor_id
        }
    )
    assert str(tool) == "<IntentTool - test_intent>"

    assert test_context.json_fragment  # To reproduce an error case in tracing
    intent_response = intent.IntentResponse("*")
    intent_response.async_set_states(
        [State("light.matched", "on")], [State("light.unmatched", "on")]
    )
    intent_response.async_set_speech("Some speech")
    intent_response.async_set_card("Card title", "card content")
    intent_response.async_set_speech_slots({"hello": 1})
    intent_response.async_set_reprompt("Do it again")
    tool_input = llm.ToolInput(
        tool_name="test_intent",
        tool_args={"area": "kitchen", "floor": "ground_floor"},
    )

    with patch(
        "homeassistant.helpers.intent.async_handle", return_value=intent_response
    ) as mock_intent_handle:
        response = await api.async_call_tool(tool_input)

    mock_intent_handle.assert_awaited_once_with(
        hass=hass,
        platform="test_platform",
        intent_type="test_intent",
        slots={
            "area": {"value": "kitchen"},
            "floor": {"value": "ground_floor"},
        },
        text_input=None,
        context=test_context,
        language="*",
        assistant="conversation",
        device_id=None,
    )
    assert response == {
        "data": {
            "failed": [],
            "success": [],
        },
        "reprompt": {
            "plain": {
                "extra_data": None,
                "reprompt": "Do it again",
            },
        },
        "response_type": "action_done",
        "speech": {
            "plain": {
                "extra_data": None,
                "speech": "Some speech",
            },
        },
        "speech_slots": {
            "hello": 1,
        },
    }

    # Call with a device/area/floor
    entry = MockConfigEntry(title=None)
    entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        connections={("test", "1234")},
        suggested_area="Test Area",
    )
    area = area_registry.async_get_area_by_name("Test Area")
    floor = floor_registry.async_create("2")
    area_registry.async_update(area.id, floor_id=floor.floor_id)
    llm_context.device_id = device.id

    with patch(
        "homeassistant.helpers.intent.async_handle", return_value=intent_response
    ) as mock_intent_handle:
        response = await api.async_call_tool(tool_input)

    mock_intent_handle.assert_awaited_once_with(
        hass=hass,
        platform="test_platform",
        intent_type="test_intent",
        slots={
            "area": {"value": "kitchen"},
            "floor": {"value": "ground_floor"},
            "preferred_area_id": {"value": area.id},
            "preferred_floor_id": {"value": floor.floor_id},
        },
        text_input=None,
        context=test_context,
        language="*",
        assistant="conversation",
        device_id=device.id,
    )
    assert response == {
        "data": {
            "failed": [],
            "success": [],
        },
        "response_type": "action_done",
        "reprompt": {
            "plain": {
                "extra_data": None,
                "reprompt": "Do it again",
            },
        },
        "speech": {
            "plain": {
                "extra_data": None,
                "speech": "Some speech",
            },
        },
        "speech_slots": {
            "hello": 1,
        },
    }