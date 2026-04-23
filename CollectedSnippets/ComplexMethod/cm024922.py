async def test_calendar_get_events_tool(hass: HomeAssistant) -> None:
    """Test the calendar get events tool."""
    assert await async_setup_component(hass, "homeassistant", {})
    hass.states.async_set(
        "calendar.test_calendar", "on", {"friendly_name": "Mock Calendar Name"}
    )
    async_expose_entity(hass, "conversation", "calendar.test_calendar", True)
    context = Context()
    llm_context = llm.LLMContext(
        platform="test_platform",
        context=context,
        language="*",
        assistant="conversation",
        device_id=None,
    )
    api = await llm.async_get_api(hass, "assist", llm_context)
    tool = next(
        (tool for tool in api.tools if tool.name == "calendar_get_events"), None
    )
    assert tool is not None
    assert tool.parameters.schema["calendar"].container == ["Mock Calendar Name"]

    calls = async_mock_service(
        hass,
        domain=calendar.DOMAIN,
        service=calendar.SERVICE_GET_EVENTS,
        schema=calendar.SERVICE_GET_EVENTS_SCHEMA,
        response={
            "calendar.test_calendar": {
                "events": [
                    {
                        "start": "2025-09-17",
                        "end": "2025-09-18",
                        "summary": "Home Assistant 12th birthday",
                        "description": "",
                    },
                    {
                        "start": "2025-09-17T14:00:00-05:00",
                        "end": "2025-09-18T15:00:00-05:00",
                        "summary": "Champagne",
                        "description": "",
                    },
                ]
            }
        },
        supports_response=SupportsResponse.ONLY,
    )

    tool_input = llm.ToolInput(
        tool_name="calendar_get_events",
        tool_args={
            "calendar": "Mock Calendar Name",
            "range": "today",
        },
    )
    now = dt_util.now()
    with patch("homeassistant.util.dt.now", return_value=now):
        response = await api.async_call_tool(tool_input)

    assert len(calls) == 1
    call = calls[0]
    assert call.domain == calendar.DOMAIN
    assert call.service == calendar.SERVICE_GET_EVENTS
    assert call.data == {
        "entity_id": ["calendar.test_calendar"],
        "start_date_time": now,
        "end_date_time": dt_util.start_of_local_day() + timedelta(days=1),
    }

    assert response == {
        "success": True,
        "result": [
            {
                "start": "2025-09-17",
                "end": "2025-09-18",
                "summary": "Home Assistant 12th birthday",
                "description": "",
                "all_day": True,
            },
            {
                "start": "2025-09-17T14:00:00-05:00",
                "end": "2025-09-18T15:00:00-05:00",
                "summary": "Champagne",
                "description": "",
            },
        ],
    }

    tool_input.tool_args["range"] = "week"
    with patch("homeassistant.util.dt.now", return_value=now):
        response = await api.async_call_tool(tool_input)

    assert len(calls) == 2
    call = calls[1]
    assert call.data == {
        "entity_id": ["calendar.test_calendar"],
        "start_date_time": now,
        "end_date_time": dt_util.start_of_local_day() + timedelta(days=7),
    }