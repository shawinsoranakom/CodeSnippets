async def test_async_get_all_descriptions(hass: HomeAssistant) -> None:
    """Test async_get_all_descriptions."""
    group_config = {GROUP_DOMAIN: {}}
    assert await async_setup_component(hass, GROUP_DOMAIN, group_config)
    assert await async_setup_component(hass, SYSTEM_HEALTH_DOMAIN, {})

    with patch(
        "homeassistant.helpers.service._load_services_files",
        side_effect=service._load_services_files,
    ) as proxy_load_services_files:
        descriptions = await service.async_get_all_descriptions(hass)

    # Test we only load services.yaml for integrations with services.yaml
    # And system_health has no services
    assert proxy_load_services_files.mock_calls[0][1][0] == unordered(
        [
            await async_get_integration(hass, GROUP_DOMAIN),
        ]
    )

    assert len(descriptions) == 1
    assert GROUP_DOMAIN in descriptions
    assert "description" not in descriptions[GROUP_DOMAIN]["reload"]
    assert "fields" in descriptions[GROUP_DOMAIN]["reload"]

    # Does not have services
    assert SYSTEM_HEALTH_DOMAIN not in descriptions

    logger_config = {LOGGER_DOMAIN: {}}

    # Test legacy service with translations in services.yaml
    def _load_services_file(integration: Integration) -> JSON_TYPE:
        return {
            "set_default_level": {
                "description": "Translated description",
                "fields": {
                    "level": {
                        "description": "Field description",
                        "example": "Field example",
                        "name": "Field name",
                        "selector": {
                            "select": {
                                "options": [
                                    "debug",
                                    "info",
                                    "warning",
                                    "error",
                                    "fatal",
                                    "critical",
                                ],
                                "translation_key": "level",
                            }
                        },
                    }
                },
                "name": "Translated name",
            },
            "set_level": None,
        }

    with patch(
        "homeassistant.helpers.service._load_services_file",
        side_effect=_load_services_file,
    ):
        await async_setup_component(hass, LOGGER_DOMAIN, logger_config)
        descriptions = await service.async_get_all_descriptions(hass)

    assert len(descriptions) == 2
    assert LOGGER_DOMAIN in descriptions
    assert descriptions[LOGGER_DOMAIN]["set_default_level"]["name"] == "Translated name"
    assert (
        descriptions[LOGGER_DOMAIN]["set_default_level"]["description"]
        == "Translated description"
    )
    assert (
        descriptions[LOGGER_DOMAIN]["set_default_level"]["fields"]["level"]["name"]
        == "Field name"
    )
    assert (
        descriptions[LOGGER_DOMAIN]["set_default_level"]["fields"]["level"][
            "description"
        ]
        == "Field description"
    )
    assert (
        descriptions[LOGGER_DOMAIN]["set_default_level"]["fields"]["level"]["example"]
        == "Field example"
    )

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
    hass.services.async_register(
        LOGGER_DOMAIN,
        "another_service_with_response",
        lambda x: None,
        None,
        SupportsResponse.OPTIONAL,
    )
    service.async_set_service_schema(
        hass,
        LOGGER_DOMAIN,
        "another_service_with_response",
        {"description": "response service"},
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
    assert "another_service_with_response" in descriptions[LOGGER_DOMAIN]
    assert descriptions[LOGGER_DOMAIN]["another_service_with_response"]["response"] == {
        "optional": True
    }

    # Verify the cache returns the same object
    assert await service.async_get_all_descriptions(hass) is descriptions