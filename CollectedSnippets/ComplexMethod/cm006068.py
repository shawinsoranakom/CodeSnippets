async def test_delete_provider_credential_cleans_up_enabled_models(client: AsyncClient, logged_in_headers):
    """Test that deleting a provider credential cleans up explicitly enabled models for that provider."""
    # Clean up any existing OPENAI_API_KEY variables
    all_vars = await client.get("api/v1/variables/", headers=logged_in_headers)
    for var in all_vars.json():
        if var.get("name") == "OPENAI_API_KEY":
            await client.delete(f"api/v1/variables/{var['id']}", headers=logged_in_headers)

    openai_variable = {
        "name": "OPENAI_API_KEY",
        "value": "sk-test-key",
        "type": CREDENTIAL_TYPE,
        "default_fields": [],
    }

    # Mock successful OpenAI API call to create credential
    with mock.patch("langchain_openai.ChatOpenAI.invoke") as mock_invoke:
        mock_invoke.return_value = "test response"
        create_response = await client.post("api/v1/variables/", json=openai_variable, headers=logged_in_headers)
        assert create_response.status_code == status.HTTP_201_CREATED
        created_var = create_response.json()

    # Enable some non-default OpenAI models (explicitly enable models that aren't default)
    with mock.patch("lfx.base.models.unified_models.validate_model_provider_key"):
        enable_response = await client.post(
            "api/v1/models/enabled_models",
            json=[
                {"provider": "OpenAI", "model_id": "gpt-4-turbo-preview", "enabled": True},
            ],
            headers=logged_in_headers,
        )
        assert enable_response.status_code == status.HTTP_200_OK

    # Delete the credential - should clean up enabled models
    delete_response = await client.delete(f"api/v1/variables/{created_var['id']}", headers=logged_in_headers)
    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify enabled models are cleaned up
    all_vars_after = await client.get("api/v1/variables/", headers=logged_in_headers)
    enabled_models_var = next(
        (v for v in all_vars_after.json() if v.get("name") == "__enabled_models__"),
        None,
    )
    # Either the variable should be gone, or it should not contain OpenAI models
    if enabled_models_var and enabled_models_var.get("value"):
        import json

        enabled_models = json.loads(enabled_models_var["value"])
        assert "gpt-4-turbo-preview" not in enabled_models