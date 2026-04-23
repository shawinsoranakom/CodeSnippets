async def test_service_descriptions(hass: HomeAssistant) -> None:
    """Test that service descriptions are loaded and reloaded correctly."""
    # Test 1: has "description" but no "fields"
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "description": "test description",
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    )

    descriptions = await async_get_all_descriptions(hass)

    assert descriptions[DOMAIN]["test"]["name"] == "test"
    assert descriptions[DOMAIN]["test"]["description"] == "test description"
    assert not descriptions[DOMAIN]["test"]["fields"]

    # Test 2: has "fields" but no "description"
    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "script": {
                "test": {
                    "fields": {
                        "test_param": {
                            "description": "test_param description",
                            "example": "test_param example",
                        }
                    },
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    descriptions = await async_get_all_descriptions(hass)

    assert descriptions[script.DOMAIN]["test"]["description"] == ""
    assert (
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["description"]
        == "test_param description"
    )
    assert (
        descriptions[script.DOMAIN]["test"]["fields"]["test_param"]["example"]
        == "test_param example"
    )

    # Test 3: has "alias" that will be used as "name"
    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={
            "script": {
                "test_name": {
                    "alias": "ABC",
                    "sequence": [{"delay": {"seconds": 5}}],
                }
            }
        },
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)

    descriptions = await async_get_all_descriptions(hass)

    assert descriptions[DOMAIN]["test_name"]["name"] == "ABC"