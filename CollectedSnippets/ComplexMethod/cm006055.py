async def test_get_config_authenticated_returns_full_config(client: AsyncClient, logged_in_headers: dict):
    """Test that authenticated /config returns full ConfigResponse with all settings."""
    response = await client.get("api/v1/config", headers=logged_in_headers)
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, dict), "The result must be a dictionary"

    # Verify type discriminator for full config
    assert "type" in result, "Response must contain 'type' discriminator field"
    assert result["type"] == "full", "Authenticated response must have type='full'"

    # Verify full config fields are present (not just public fields)
    assert "auto_saving" in result, "Authenticated response must contain 'auto_saving'"
    assert "auto_saving_interval" in result, "Authenticated response must contain 'auto_saving_interval'"
    assert "health_check_max_retries" in result, "Authenticated response must contain 'health_check_max_retries'"
    assert "feature_flags" in result, "Authenticated response must contain 'feature_flags'"