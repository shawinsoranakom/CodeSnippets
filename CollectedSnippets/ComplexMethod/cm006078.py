async def test_provider_variable_mapping_multi_variable_provider(client: AsyncClient, logged_in_headers):
    """Test that IBM WatsonX returns multiple required variables."""
    response = await client.get("api/v1/models/provider-variable-mapping", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK

    # Check IBM WatsonX has multiple variables
    watsonx_vars = result.get("IBM WatsonX", [])
    assert len(watsonx_vars) >= 3  # API Key, Project ID, URL

    # Find each variable
    var_keys = {v["variable_key"] for v in watsonx_vars}
    assert "WATSONX_APIKEY" in var_keys
    assert "WATSONX_PROJECT_ID" in var_keys
    assert "WATSONX_URL" in var_keys

    # Check API Key is secret
    api_key_var = next((v for v in watsonx_vars if v["variable_key"] == "WATSONX_APIKEY"), None)
    assert api_key_var is not None
    assert api_key_var["is_secret"] is True
    assert api_key_var["required"] is True

    # Check Project ID is not secret
    project_id_var = next((v for v in watsonx_vars if v["variable_key"] == "WATSONX_PROJECT_ID"), None)
    assert project_id_var is not None
    assert project_id_var["is_secret"] is False
    assert project_id_var["required"] is True

    # Check URL has options
    url_var = next((v for v in watsonx_vars if v["variable_key"] == "WATSONX_URL"), None)
    assert url_var is not None
    assert url_var["is_secret"] is False
    assert url_var["required"] is True
    assert len(url_var["options"]) > 0  # Should have regional endpoint options
    assert "https://us-south.ml.cloud.ibm.com" in url_var["options"]