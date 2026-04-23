def test_process_routes_prompts(sample_app, mock_system_service):
    """Test that prompt definitions are correctly generated."""
    processed = process_fastapi_routes_for_mcp(sample_app, None)
    assert len(processed.prompt_definitions) == 1
    prompt = processed.prompt_definitions[0]
    assert prompt["name"] == "test_prompt"
    assert len(prompt["arguments"]) == 2
    arg_map = {a["name"]: a for a in prompt["arguments"]}
    assert arg_map["arg1"]["type"] == "str"
    assert arg_map["arg2"]["default"] == 42
    assert prompt["tags"] == ["/api/v1/prompts/test"]