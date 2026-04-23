async def test_variables_credential_redaction(client: AsyncClient, openai_credential, logged_in_headers):
    """Test that credential variables have credentials properly redacted."""
    # Clean up any existing OPENAI_API_KEY variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    openai_var_name = _provider_variable_mapping.get("OpenAI")
    for var in all_vars.json():
        if var.get("name") == openai_var_name:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    # Create a credential using variables endpoint
    variable_payload = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    # Mock API validation
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        create_response = await client.post("api/v1/variables/", json=variable_payload, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED
    created_credential = create_response.json()

    # Get all variables
    response = await client.get("api/v1/variables/", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, list)

    # Find the created credential in the response
    credential_variables = [v for v in result if v.get("id") == created_credential["id"]]
    assert len(credential_variables) == 1

    credential_variable = credential_variables[0]

    # Verify credential is redacted (value should be None for CREDENTIAL_TYPE)
    assert credential_variable["value"] is None
    assert credential_variable["type"] == CREDENTIAL_TYPE