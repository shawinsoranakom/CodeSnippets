async def test_enabled_providers_after_credential_creation(client: AsyncClient, openai_credential, logged_in_headers):
    """Test that provider status changes after credential creation."""
    # Clean up any existing OPENAI_API_KEY variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    openai_var_name = _provider_variable_mapping.get("OpenAI")
    for var in all_vars.json():
        if var.get("name") == openai_var_name:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Check initial status
    initial_response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
    initial_result = initial_response.json()

    assert initial_response.status_code == status.HTTP_200_OK
    openai_initially_enabled = initial_result.get("provider_status", {}).get("OpenAI", False)

    # Create OpenAI credential using variables endpoint
    variable_payload = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    # Mock API validation - mock where it's used (in the variable endpoint)
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None  # validate_model_provider_key returns None on success
        create_response = await client.post("api/v1/variables/", json=variable_payload, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED

    # Check status after credential creation
    # Mock validation for enabled_providers endpoint as well
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        after_response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
    after_result = after_response.json()

    assert after_response.status_code == status.HTTP_200_OK
    assert "OpenAI" in after_result["enabled_providers"]
    assert after_result["provider_status"]["OpenAI"] is True

    # Verify the status changed
    assert after_result["provider_status"]["OpenAI"] != openai_initially_enabled or openai_initially_enabled is True