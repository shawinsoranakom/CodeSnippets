async def test_variables_multiple_credentials_all_redacted(
    client: AsyncClient, openai_credential, anthropic_credential, logged_in_headers
):
    """Test that all credentials are redacted when fetching all variables."""
    # Clean up any existing variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    var_names = {
        _provider_variable_mapping.get("OpenAI"),
        _provider_variable_mapping.get("Anthropic"),
    }
    for var in all_vars.json():
        if var.get("name") in var_names:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create multiple credentials using variables endpoint
    openai_var = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    anthropic_var = _create_variable_payload(anthropic_credential["provider"], anthropic_credential["value"])

    # Mock API validations
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        create_response1 = await client.post("api/v1/variables/", json=openai_var, headers=logged_in_headers)
        create_response2 = await client.post("api/v1/variables/", json=anthropic_var, headers=logged_in_headers)

    assert create_response1.status_code == status.HTTP_201_CREATED
    assert create_response2.status_code == status.HTTP_201_CREATED

    # Get all variables
    response = await client.get("api/v1/variables/", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK

    # Verify all credentials are redacted
    for variable in result:
        if variable.get("type") == CREDENTIAL_TYPE:
            # Credential values should be None (redacted)
            assert variable["value"] is None