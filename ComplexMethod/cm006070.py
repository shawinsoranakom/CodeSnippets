async def test_enabled_providers_multiple_credentials(
    client: AsyncClient, openai_credential, anthropic_credential, google_credential, logged_in_headers
):
    """Test provider status with multiple credentials."""
    # Clean up any existing variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    var_names = {
        _provider_variable_mapping.get("OpenAI"),
        _provider_variable_mapping.get("Anthropic"),
        _provider_variable_mapping.get("Google Generative AI"),
    }
    for var in all_vars.json():
        if var.get("name") in var_names:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create multiple credentials using variables endpoint
    openai_var = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    anthropic_var = _create_variable_payload(anthropic_credential["provider"], anthropic_credential["value"])
    google_var = _create_variable_payload(google_credential["provider"], google_credential["value"])

    # Mock API validations
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        await client.post("api/v1/variables/", json=openai_var, headers=logged_in_headers)
        await client.post("api/v1/variables/", json=anthropic_var, headers=logged_in_headers)
        await client.post("api/v1/variables/", json=google_var, headers=logged_in_headers)

    # Check enabled providers - mock validation for enabled_providers endpoint
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert "OpenAI" in result["enabled_providers"]
    assert "Anthropic" in result["enabled_providers"]
    assert "Google Generative AI" in result["enabled_providers"]

    assert result["provider_status"]["OpenAI"] is True
    assert result["provider_status"]["Anthropic"] is True
    assert result["provider_status"]["Google Generative AI"] is True