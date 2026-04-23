async def test_security_credential_value_never_exposed_in_variables_endpoint(
    client: AsyncClient, openai_credential, logged_in_headers
):
    """Critical security test: ensure credential values are NEVER exposed in plain text."""
    # Clean up any existing OPENAI_API_KEY variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    openai_var_name = _provider_variable_mapping.get("OpenAI")
    for var in all_vars.json():
        if var.get("name") == openai_var_name:
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    original_value = openai_credential["value"]

    # Create credential using variables endpoint
    variable_payload = _create_variable_payload(openai_credential["provider"], openai_credential["value"])
    # Mock API validation
    with mock.patch("langflow.api.v1.variable.validate_model_provider_key") as mock_validate:
        mock_validate.return_value = None
        create_response = await client.post("api/v1/variables/", json=variable_payload, headers=logged_in_headers)
    assert create_response.status_code == status.HTTP_201_CREATED

    # Get all variables - this is the security-critical path
    response = await client.get("api/v1/variables/", headers=logged_in_headers)
    result = response.json()

    # CRITICAL: Original value must NEVER appear in response
    response_text = str(result)
    assert original_value not in response_text

    # Verify each credential is properly redacted (set to None)
    for variable in result:
        if variable.get("type") == CREDENTIAL_TYPE:
            # CRITICAL: Value must be None (redacted), never the original value
            assert variable["value"] is None