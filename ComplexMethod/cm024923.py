async def test_todo_get_items_tool(hass: HomeAssistant) -> None:
    """Test the todo get items tool."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "todo", {})
    hass.states.async_set(
        "todo.test_list", "0", {"friendly_name": "Mock Todo List Name"}
    )
    async_expose_entity(hass, "conversation", "todo.test_list", True)
    context = Context()
    llm_context = llm.LLMContext(
        platform="test_platform",
        context=context,
        language="*",
        assistant="conversation",
        device_id=None,
    )
    api = await llm.async_get_api(hass, "assist", llm_context)
    tool = next((tool for tool in api.tools if tool.name == "todo_get_items"), None)
    assert tool is not None
    assert tool.parameters.schema["todo_list"].container == ["Mock Todo List Name"]

    calls = async_mock_service(
        hass,
        domain=todo.DOMAIN,
        service=todo.TodoServices.GET_ITEMS,
        schema=cv.make_entity_service_schema(todo.TODO_SERVICE_GET_ITEMS_SCHEMA),
        response={
            "todo.test_list": {
                "items": [
                    {
                        "uid": "1234",
                        "summary": "Buy milk",
                        "status": "needs_action",
                    },
                    {
                        "uid": "5678",
                        "summary": "Call mom",
                        "status": "needs_action",
                        "due": "2025-09-17",
                        "description": "Remember birthday",
                    },
                ]
            }
        },
    )

    # Test without status filter (defaults to needs_action)
    result = await tool.async_call(
        hass,
        llm.ToolInput("todo_get_items", {"todo_list": "Mock Todo List Name"}),
        llm_context,
    )

    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": ["todo.test_list"],
        "status": ["needs_action"],
    }
    assert result == {
        "success": True,
        "result": [
            {
                "uid": "1234",
                "status": "needs_action",
                "summary": "Buy milk",
            },
            {
                "uid": "5678",
                "status": "needs_action",
                "summary": "Call mom",
                "due": "2025-09-17",
                "description": "Remember birthday",
            },
        ],
    }

    # Test that the status filter is passed correctly to the service call.
    # We don't assert on the response since it is fixed above.
    calls.clear()
    result = await tool.async_call(
        hass,
        llm.ToolInput(
            "todo_get_items",
            {"todo_list": "Mock Todo List Name", "status": "completed"},
        ),
        llm_context,
    )
    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": ["todo.test_list"],
        "status": ["completed"],
    }

    # Test that the status filter is passed correctly to the service call.
    # We don't assert on the response since it is fixed above.
    calls.clear()
    result = await tool.async_call(
        hass,
        llm.ToolInput(
            "todo_get_items",
            {"todo_list": "Mock Todo List Name", "status": "all"},
        ),
        llm_context,
    )
    assert len(calls) == 1
    assert calls[0].data == {
        "entity_id": ["todo.test_list"],
        "status": ["needs_action", "completed"],
    }