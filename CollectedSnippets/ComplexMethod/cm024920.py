async def test_script_tool(
    hass: HomeAssistant,
    entity_registry: er.EntityRegistry,
    area_registry: ar.AreaRegistry,
    floor_registry: fr.FloorRegistry,
) -> None:
    """Test ScriptTool for the assist API."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, "intent", {})
    context = Context()
    llm_context = llm.LLMContext(
        platform="test_platform",
        context=context,
        language="*",
        assistant="conversation",
        device_id=None,
    )

    # Create a script with a unique ID
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test_script": {
                    "alias": "test script",
                    "description": "This is a test script",
                    "sequence": [
                        {"variables": {"result": {"drinks": 2}}},
                        {"stop": True, "response_variable": "result"},
                    ],
                    "fields": {
                        "beer": {"description": "Number of beers", "required": True},
                        "wine": {"selector": {"number": {"min": 0, "max": 3}}},
                        "where": {"selector": {"area": {}}},
                        "area_list": {"selector": {"area": {"multiple": True}}},
                        "floor": {"selector": {"floor": {}}},
                        "floor_list": {"selector": {"floor": {"multiple": True}}},
                        "extra_field": {"selector": {"area": {}}},
                    },
                },
                "script_with_no_fields": {
                    "alias": "test script 2",
                    "description": "This is another test script",
                    "sequence": [],
                },
                "unexposed_script": {
                    "sequence": [],
                },
            }
        },
    )
    async_expose_entity(hass, "conversation", "script.test_script", True)
    async_expose_entity(hass, "conversation", "script.script_with_no_fields", True)

    entity_registry.async_update_entity(
        "script.test_script",
        name="script name",
        aliases=[er.COMPUTED_NAME, "script alias"],
    )

    area = area_registry.async_create("Living room")
    floor = floor_registry.async_create("2")

    assert llm.ACTION_PARAMETERS_CACHE not in hass.data

    api = await llm.async_get_api(hass, "assist", llm_context)

    tools = [tool for tool in api.tools if isinstance(tool, llm.ScriptTool)]
    assert len(tools) == 2

    tool = tools[0]
    assert tool.name == "test_script"
    assert (
        tool.description
        == "This is a test script. Aliases: ['script name', 'script alias']"
    )
    schema = {
        vol.Required("beer", description="Number of beers"): cv.string,
        vol.Optional("wine"): selector.NumberSelector({"min": 0, "max": 3}),
        vol.Optional("where"): selector.AreaSelector(),
        vol.Optional("area_list"): selector.AreaSelector({"multiple": True}),
        vol.Optional("floor"): selector.FloorSelector(),
        vol.Optional("floor_list"): selector.FloorSelector({"multiple": True}),
        vol.Optional("extra_field"): selector.AreaSelector(),
    }
    assert tool.parameters.schema == schema

    assert hass.data[llm.ACTION_PARAMETERS_CACHE]["script"] == {
        "test_script": (
            "This is a test script. Aliases: ['script name', 'script alias']",
            vol.Schema(schema),
        ),
        "script_with_no_fields": (
            "This is another test script. Aliases: ['test script 2']",
            vol.Schema({}),
        ),
    }

    # Test script with response
    tool_input = llm.ToolInput(
        tool_name="test_script",
        tool_args={
            "beer": "3",
            "wine": 0,
            "where": "Living room",
            "area_list": ["Living room"],
            "floor": "2",
            "floor_list": ["2"],
        },
    )

    with patch(
        "homeassistant.core.ServiceRegistry.async_call",
        side_effect=hass.services.async_call,
    ) as mock_service_call:
        response = await api.async_call_tool(tool_input)

    mock_service_call.assert_awaited_once_with(
        "script",
        "test_script",
        {
            "beer": "3",
            "wine": 0,
            "where": area.id,
            "area_list": [area.id],
            "floor": floor.floor_id,
            "floor_list": [floor.floor_id],
        },
        context=context,
        blocking=True,
        return_response=True,
    )
    assert response == {
        "success": True,
        "result": {"drinks": 2},
    }

    # Test script with no response
    tool_input = llm.ToolInput(
        tool_name="script_with_no_fields",
        tool_args={},
    )

    with patch(
        "homeassistant.core.ServiceRegistry.async_call",
        side_effect=hass.services.async_call,
    ) as mock_service_call:
        response = await api.async_call_tool(tool_input)

    mock_service_call.assert_awaited_once_with(
        "script",
        "script_with_no_fields",
        {},
        context=context,
        blocking=True,
        return_response=True,
    )
    assert response == {
        "success": True,
        "result": {},
    }

    # Test reload script with new parameters
    config = {
        "script": {
            "test_script": ScriptConfig(
                {
                    "description": "This is a new test script",
                    "sequence": [],
                    "mode": "single",
                    "max": 2,
                    "max_exceeded": "WARNING",
                    "trace": {},
                    "fields": {
                        "beer": {"description": "Number of beers", "required": True},
                    },
                }
            )
        }
    }

    with patch(
        "homeassistant.helpers.entity_component.EntityComponent.async_prepare_reload",
        return_value=config,
    ):
        await hass.services.async_call("script", "reload", blocking=True)

    assert hass.data[llm.ACTION_PARAMETERS_CACHE]["script"] == {}

    api = await llm.async_get_api(hass, "assist", llm_context)

    tools = [tool for tool in api.tools if isinstance(tool, llm.ScriptTool)]
    assert len(tools) == 2

    tool = tools[0]
    assert tool.name == "test_script"
    assert (
        tool.description
        == "This is a new test script. Aliases: ['script name', 'script alias']"
    )
    schema = {vol.Required("beer", description="Number of beers"): cv.string}
    assert tool.parameters.schema == schema

    assert hass.data[llm.ACTION_PARAMETERS_CACHE]["script"] == {
        "test_script": (
            "This is a new test script. Aliases: ['script name', 'script alias']",
            vol.Schema(schema),
        ),
        "script_with_no_fields": (
            "This is another test script. Aliases: ['test script 2']",
            vol.Schema({}),
        ),
    }