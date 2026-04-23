async def test_async_get_all_descriptions_failing_integration(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test async_get_all_descriptions when async_get_integrations returns an exception."""
    group_config = {GROUP_DOMAIN: {}}
    await async_setup_component(hass, GROUP_DOMAIN, group_config)

    logger_config = {LOGGER_DOMAIN: {}}
    await async_setup_component(hass, LOGGER_DOMAIN, logger_config)

    input_button_config = {INPUT_BUTTON_DOMAIN: {}}
    await async_setup_component(hass, INPUT_BUTTON_DOMAIN, input_button_config)

    async def wrap_get_integrations(
        hass: HomeAssistant, domains: Iterable[str]
    ) -> dict[str, Integration | Exception]:
        integrations = await async_get_integrations(hass, domains)
        integrations[LOGGER_DOMAIN] = ImportError("Failed to load services.yaml")
        return integrations

    with (
        patch(
            "homeassistant.helpers.service.async_get_integrations",
            wraps=wrap_get_integrations,
        ),
    ):
        descriptions = await service.async_get_all_descriptions(hass)

    assert len(descriptions) == 3
    assert "Failed to load services.yaml for integration: logger" in caplog.text

    # Services are empty defaults if the load fails but should
    # not raise
    assert "description" not in descriptions[GROUP_DOMAIN]["remove"]
    assert descriptions[GROUP_DOMAIN]["remove"]["fields"]

    assert descriptions[LOGGER_DOMAIN]["set_level"] == {"fields": {}}

    assert "description" not in descriptions[INPUT_BUTTON_DOMAIN]["press"]
    assert descriptions[INPUT_BUTTON_DOMAIN]["press"]["fields"] == {}
    assert "target" in descriptions[INPUT_BUTTON_DOMAIN]["press"]

    hass.services.async_register(LOGGER_DOMAIN, "new_service", lambda x: None, None)
    service.async_set_service_schema(
        hass, LOGGER_DOMAIN, "new_service", {"description": "new service"}
    )
    descriptions = await service.async_get_all_descriptions(hass)
    assert "description" in descriptions[LOGGER_DOMAIN]["new_service"]
    assert descriptions[LOGGER_DOMAIN]["new_service"]["description"] == "new service"

    hass.services.async_register(
        LOGGER_DOMAIN, "another_new_service", lambda x: None, None
    )
    hass.services.async_register(
        LOGGER_DOMAIN,
        "service_with_optional_response",
        lambda x: None,
        None,
        SupportsResponse.OPTIONAL,
    )
    hass.services.async_register(
        LOGGER_DOMAIN,
        "service_with_only_response",
        lambda x: None,
        None,
        SupportsResponse.ONLY,
    )

    descriptions = await service.async_get_all_descriptions(hass)
    assert "another_new_service" in descriptions[LOGGER_DOMAIN]
    assert "service_with_optional_response" in descriptions[LOGGER_DOMAIN]
    assert descriptions[LOGGER_DOMAIN]["service_with_optional_response"][
        "response"
    ] == {"optional": True}
    assert "service_with_only_response" in descriptions[LOGGER_DOMAIN]
    assert descriptions[LOGGER_DOMAIN]["service_with_only_response"]["response"] == {
        "optional": False
    }

    # Verify the cache returns the same object
    assert await service.async_get_all_descriptions(hass) is descriptions