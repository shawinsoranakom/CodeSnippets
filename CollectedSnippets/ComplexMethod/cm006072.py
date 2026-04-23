async def test_enabled_providers_filter_by_specific_providers(
    client: AsyncClient, openai_credential, anthropic_credential, logged_in_headers
):
    """Test filtering enabled_providers by specific providers."""
    # Clean up any existing variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    var_names = {
        _provider_variable_mapping.get("OpenAI"),
        _provider_variable_mapping.get("Anthropic"),
    }
    for var in all_vars.json():
        if var.get("name") in var_names:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create credentials using variables endpoint
    openai_var = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    anthropic_var = _create_variable_payload(anthropic_credential["provider"], anthropic_credential["value"])

    # Mock API validations
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        await client.post("api/v1/variables/", json=openai_var, headers=logged_in_headers)
        await client.post("api/v1/variables/", json=anthropic_var, headers=logged_in_headers)

    # Request specific providers (only providers that are in the mapping) - mock validation
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        response = await client.get(
            "api/v1/models/enabled_providers?providers=OpenAI&providers=Anthropic", headers=logged_in_headers
        )
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "OpenAI" in result["enabled_providers"]
    assert "Anthropic" in result["enabled_providers"]
    assert "OpenAI" in result["provider_status"]
    assert result["provider_status"]["OpenAI"] is True
    assert "Anthropic" in result["provider_status"]
    assert result["provider_status"]["Anthropic"] is True

    # Test filtering with non-existent provider (should not error, just return empty)
    response2 = await client.get(
        "api/v1/models/enabled_providers?providers=NonExistentProvider", headers=logged_in_headers
    )
    result2 = response2.json()
    assert response2.status_code == status.HTTP_200_OK
    assert result2["enabled_providers"] == []
    # NonExistentProvider is not in the mapping, so it won't be in provider_status
    assert "NonExistentProvider" not in result2["provider_status"]