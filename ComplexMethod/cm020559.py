async def test_generate_data_service_structure_fields(
    hass: HomeAssistant,
    init_components: None,
    mock_ai_task_entity: MockAITaskEntity,
) -> None:
    """Test the entity can generate structured data with a top level object schema."""
    result = await hass.services.async_call(
        "ai_task",
        "generate_data",
        {
            "task_name": "Profile Generation",
            "instructions": "Please generate a profile for a new user",
            "entity_id": TEST_ENTITY_ID,
            "structure": {
                "name": {
                    "description": "First and last name of the user such as Alice Smith",
                    "required": True,
                    "selector": {"text": {}},
                },
                "age": {
                    "description": "Age of the user",
                    "selector": {
                        "number": {
                            "min": 0,
                            "max": 120,
                        }
                    },
                },
            },
        },
        blocking=True,
        return_response=True,
    )
    # Arbitrary data returned by the mock entity (not determined by above schema in test)
    assert result["data"] == {
        "name": "Tracy Chen",
        "age": 30,
    }

    assert mock_ai_task_entity.mock_generate_data_tasks
    task = mock_ai_task_entity.mock_generate_data_tasks[0]
    assert task.instructions == "Please generate a profile for a new user"
    assert task.structure
    assert isinstance(task.structure, vol.Schema)
    schema = list(task.structure.schema.items())
    assert len(schema) == 2

    name_key, name_value = schema[0]
    assert name_key == "name"
    assert isinstance(name_key, vol.Required)
    assert name_key.description == "First and last name of the user such as Alice Smith"
    assert isinstance(name_value, selector.TextSelector)

    age_key, age_value = schema[1]
    assert age_key == "age"
    assert isinstance(age_key, vol.Optional)
    assert age_key.description == "Age of the user"
    assert isinstance(age_value, selector.NumberSelector)
    assert age_value.config["min"] == 0
    assert age_value.config["max"] == 120