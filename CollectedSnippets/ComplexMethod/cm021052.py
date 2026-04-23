async def test_service_registration_response_types(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test that services are registered with correct SupportsResponse types."""
    services = [
        UserService(
            name="none_service",
            key=1,
            args=[],
            supports_response=SupportsResponseType.NONE,
        ),
        UserService(
            name="optional_service",
            key=2,
            args=[],
            supports_response=SupportsResponseType.OPTIONAL,
        ),
        UserService(
            name="only_service",
            key=3,
            args=[],
            supports_response=SupportsResponseType.ONLY,
        ),
        UserService(
            name="status_service",
            key=4,
            args=[],
            supports_response=SupportsResponseType.STATUS,
        ),
    ]

    await mock_esphome_device(
        mock_client=mock_client,
        user_service=services,
        device_info={"name": "test"},
    )
    await hass.async_block_till_done()

    # Verify all services are registered
    assert hass.services.has_service(DOMAIN, "test_none_service")
    assert hass.services.has_service(DOMAIN, "test_optional_service")
    assert hass.services.has_service(DOMAIN, "test_only_service")
    assert hass.services.has_service(DOMAIN, "test_status_service")

    # Verify response types are correctly mapped using public API
    # NONE -> SupportsResponse.NONE
    # OPTIONAL -> SupportsResponse.OPTIONAL
    # ONLY -> SupportsResponse.ONLY
    # STATUS -> SupportsResponse.NONE (no data returned to HA)
    assert (
        hass.services.supports_response(DOMAIN, "test_none_service")
        == SupportsResponse.NONE
    )
    assert (
        hass.services.supports_response(DOMAIN, "test_optional_service")
        == SupportsResponse.OPTIONAL
    )
    assert (
        hass.services.supports_response(DOMAIN, "test_only_service")
        == SupportsResponse.ONLY
    )
    assert (
        hass.services.supports_response(DOMAIN, "test_status_service")
        == SupportsResponse.NONE
    )