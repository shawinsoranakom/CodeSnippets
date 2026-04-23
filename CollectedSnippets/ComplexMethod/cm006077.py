async def test_provider_variable_mapping_returns_full_variable_info(client: AsyncClient, logged_in_headers):
    """Test that provider-variable-mapping endpoint returns full variable info for each provider."""
    response = await client.get("api/v1/models/provider-variable-mapping", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, dict)

    # Check that known providers exist
    assert "OpenAI" in result
    assert "Anthropic" in result
    assert "Google Generative AI" in result
    assert "Ollama" in result
    assert "IBM WatsonX" in result

    # Check structure of variables for OpenAI (single variable provider)
    openai_vars = result["OpenAI"]
    assert isinstance(openai_vars, list)
    assert len(openai_vars) >= 1

    # Check each variable has required fields
    for var in openai_vars:
        assert "variable_name" in var
        assert "variable_key" in var
        assert "required" in var
        assert "is_secret" in var
        assert "is_list" in var
        assert "options" in var

    # Check OpenAI primary variable (order-independent)
    openai_api_key_var = next((v for v in openai_vars if v["variable_key"] == "OPENAI_API_KEY"), None)
    assert openai_api_key_var is not None
    assert openai_api_key_var["required"] is True
    assert openai_api_key_var["is_secret"] is True