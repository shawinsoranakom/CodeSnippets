async def test_get_config_unauthenticated_returns_expected_fields(client: AsyncClient):
    """Test that unauthenticated /config response contains only public-safe fields."""
    response = await client.get("api/v1/config")
    result = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(result, dict), "The result must be a dictionary"

    # Verify expected public fields are present
    assert "max_file_size_upload" in result, "Response must contain 'max_file_size_upload'"
    assert "event_delivery" in result, "Response must contain 'event_delivery'"
    assert "feature_flags" in result, "Response must contain 'feature_flags'"
    assert "voice_mode_available" in result, "Response must contain 'voice_mode_available'"
    assert "frontend_timeout" in result, "Response must contain 'frontend_timeout'"

    # Verify type discriminator for public config
    assert "type" in result, "Response must contain 'type' discriminator field"
    assert result["type"] == "public", "Unauthenticated response must have type='public'"