async def test_get_config_unauthenticated_returns_correct_field_types(client: AsyncClient):
    """Test that unauthenticated /config response fields have correct types."""
    response = await client.get("api/v1/config")
    result = response.json()

    assert response.status_code == status.HTTP_200_OK

    # Verify field types
    assert isinstance(result["max_file_size_upload"], int), "max_file_size_upload must be an integer"
    assert isinstance(result["frontend_timeout"], int), "frontend_timeout must be an integer"
    assert isinstance(result["voice_mode_available"], bool), "voice_mode_available must be a boolean"
    assert isinstance(result["feature_flags"], dict), "feature_flags must be an object"
    assert result["feature_flags"].get("wxo_deployments") is False, "wxo_deployments flag should default to false"
    assert result["event_delivery"] in ["polling", "streaming", "direct"], (
        "event_delivery must be one of: polling, streaming, direct"
    )