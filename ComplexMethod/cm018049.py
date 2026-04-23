async def test_service_registry_service_enumeration(hass: HomeAssistant) -> None:
    """Test enumerating services methods."""
    hass.services.async_register("test_domain", "test_service", lambda call: None)
    services1 = hass.services.async_services()
    services2 = hass.services.async_services()
    assert len(services1) == 1
    assert services1 == services2
    assert services1 is not services2  # should be a copy

    services1 = hass.services.async_services_internal()
    services2 = hass.services.async_services_internal()
    assert len(services1) == 1
    assert services1 == services2
    assert services1 is services2  # should be the same object

    assert hass.services.async_services_for_domain("unknown") == {}

    services1 = hass.services.async_services_for_domain("test_domain")
    services2 = hass.services.async_services_for_domain("test_domain")
    assert len(services1) == 1
    assert services1 == services2
    assert services1 is not services2