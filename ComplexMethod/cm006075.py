async def test_enabled_providers_reflects_models_endpoint(client: AsyncClient, openai_credential, logged_in_headers):
    """Test that /models endpoint reflects same is_enabled status as /enabled_providers."""
    # Clean up any existing OPENAI_API_KEY variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    openai_var_name = _provider_variable_mapping.get("OpenAI")
    for var in all_vars.json():
        if var.get("name") == openai_var_name:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create credential using variables endpoint
    variable_payload = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    # Mock API validation
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        await client.post("api/v1/variables/", json=variable_payload, headers=logged_in_headers)

    # Get enabled providers and models - mock validation in unified_models so providers are marked enabled
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None

        enabled_response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
        enabled_result = enabled_response.json()

        # Get models (which should include provider information)
        models_response = await client.get("api/v1/models", headers=logged_in_headers)
        models_result = models_response.json()

    assert models_response.status_code == status.HTTP_200_OK

    # Check that OpenAI models have is_enabled=True
    openai_models = [m for m in models_result if m.get("provider") == "OpenAI"]
    if openai_models:
        for model in openai_models:
            assert model.get("is_enabled") is True

    # Verify consistency with enabled_providers
    assert enabled_result["provider_status"]["OpenAI"] is True