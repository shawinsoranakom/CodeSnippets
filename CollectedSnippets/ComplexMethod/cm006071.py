async def test_enabled_providers_after_credential_deletion(client: AsyncClient, openai_credential, logged_in_headers):
    """Test that provider status updates after credential deletion."""
    # Get initial OpenAI credentials to clean up (using variables endpoint)
    all_variables = await client.get("api/v1/variables/", headers=logged_in_headers)
    openai_var_name = _provider_variable_mapping.get("OpenAI")
    for var in all_variables.json():
        if var.get("name") == openai_var_name:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create credential using variables endpoint
    variable_payload = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    # Mock API validation
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        create_response = await client.post("api/v1/variables/", json=variable_payload, headers=logged_in_headers)
    created_credential = create_response.json()
    credential_id = created_credential["id"]

    # Verify enabled - mock validation for enabled_providers endpoint as well
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        enabled_response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
    enabled_result = enabled_response.json()
    assert "OpenAI" in enabled_result["enabled_providers"]
    assert enabled_result["provider_status"]["OpenAI"] is True

    # Delete credential
    delete_response = await client.delete(f"api/v1/variables/{credential_id}", headers=logged_in_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify disabled
    disabled_response = await client.get("api/v1/models/enabled_providers", headers=logged_in_headers)
    disabled_result = disabled_response.json()
    assert "OpenAI" not in disabled_result["enabled_providers"]
    # When no credentials exist, provider_status may be empty or OpenAI should be False
    assert disabled_result["provider_status"].get("OpenAI", False) is False