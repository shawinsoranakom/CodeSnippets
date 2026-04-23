async def test_async_get_all_descriptions_new_service_added_while_loading(
    hass: HomeAssistant,
) -> None:
    """Test async_get_all_descriptions when a new service is added while loading translations."""
    group_config = {GROUP_DOMAIN: {}}
    await async_setup_component(hass, GROUP_DOMAIN, group_config)
    descriptions = await service.async_get_all_descriptions(hass)

    assert len(descriptions) == 1

    assert "description" not in descriptions["group"]["reload"]
    assert "fields" in descriptions["group"]["reload"]

    logger_domain = LOGGER_DOMAIN
    logger_config = {logger_domain: {}}

    translations_called = threading.Event()
    translations_wait = threading.Event()

    def _load_services_file(integration: Integration) -> JSON_TYPE:
        translations_called.set()
        translations_wait.wait()
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
        await async_setup_component(hass, logger_domain, logger_config)
        task = asyncio.create_task(service.async_get_all_descriptions(hass))
        await hass.async_add_executor_job(translations_called.wait)
        # Now register a new service while translations are being loaded
        hass.services.async_register(logger_domain, "new_service", lambda x: None, None)
        service.async_set_service_schema(
            hass, logger_domain, "new_service", {"description": "new service"}
        )
        translations_wait.set()
        descriptions = await task

    # Two domains should be present
    assert len(descriptions) == 2

    logger_descriptions = descriptions[logger_domain]

    # The new service was loaded after the translations were loaded
    # so it should not appear until the next time we fetch
    assert "new_service" not in logger_descriptions

    set_default_level = logger_descriptions["set_default_level"]

    assert set_default_level["name"] == "Translated name"
    assert set_default_level["description"] == "Translated description"
    set_default_level_fields = set_default_level["fields"]
    assert set_default_level_fields["level"]["name"] == "Field name"
    assert set_default_level_fields["level"]["description"] == "Field description"
    assert set_default_level_fields["level"]["example"] == "Field example"

    descriptions = await service.async_get_all_descriptions(hass)
    assert "description" in descriptions[logger_domain]["new_service"]
    assert descriptions[logger_domain]["new_service"]["description"] == "new service"