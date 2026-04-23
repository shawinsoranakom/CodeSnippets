async def test_async_get_all_descriptions(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sun_condition_descriptions: str,
) -> None:
    """Test async_get_all_descriptions."""
    device_automation_condition_descriptions = """
        _device:
          fields:
            entity:
              selector:
                entity:
                  filter:
                    domain: alarm_control_panel
                    supported_features:
                      - alarm_control_panel.AlarmControlPanelEntityFeature.ARM_HOME
        """
    light_condition_descriptions = """
        is_off:
          target:
            entity:
              domain: light
        is_on:
          target:
            entity:
              domain: light
        is_brightness:
          target:
            entity:
              domain: light
        """

    ws_client = await hass_ws_client(hass)

    assert await async_setup_component(hass, SUN_DOMAIN, {})
    assert await async_setup_component(hass, SYSTEM_HEALTH_DOMAIN, {})
    await hass.async_block_till_done()

    def _load_yaml(fname, secrets=None):
        if fname.endswith("device_automation/conditions.yaml"):
            condition_descriptions = device_automation_condition_descriptions
        elif fname.endswith("light/conditions.yaml"):
            condition_descriptions = light_condition_descriptions
        elif fname.endswith("sun/conditions.yaml"):
            condition_descriptions = sun_condition_descriptions
        with io.StringIO(condition_descriptions) as file:
            return parse_yaml(file)

    with (
        patch(
            "homeassistant.helpers.condition._load_conditions_files",
            side_effect=condition._load_conditions_files,
        ) as proxy_load_conditions_files,
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_conditions", return_value=True),
    ):
        descriptions = await condition.async_get_all_descriptions(hass)

    # Test we only load conditions.yaml for integrations with conditions,
    # system_health has no conditions
    assert proxy_load_conditions_files.mock_calls[0][1][0] == unordered(
        [
            await async_get_integration(hass, SUN_DOMAIN),
        ]
    )

    # system_health does not have conditions and should not be in descriptions
    expected_descriptions = {
        "sun": {
            "fields": {
                "after": {
                    "example": "sunrise",
                    "selector": {
                        "select": {
                            "custom_value": False,
                            "multiple": False,
                            "options": ["sunrise", "sunset"],
                            "sort": False,
                        }
                    },
                },
                "after_offset": {"selector": {"time": {}}},
                "before": {
                    "example": "sunrise",
                    "selector": {
                        "select": {
                            "custom_value": False,
                            "multiple": False,
                            "options": ["sunrise", "sunset"],
                            "sort": False,
                        }
                    },
                },
                "before_offset": {"selector": {"time": {}}},
            }
        }
    }
    assert descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await condition.async_get_all_descriptions(hass) is descriptions

    # Load the device_automation integration and check a new cache object is created
    assert await async_setup_component(hass, DEVICE_AUTOMATION_DOMAIN, {})
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_conditions", return_value=True),
    ):
        new_descriptions = await condition.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The device automation conditions should now be present
    expected_descriptions |= {
        "device": {
            "fields": {
                "entity": {
                    "selector": {
                        "entity": {
                            "filter": [
                                {
                                    "domain": ["alarm_control_panel"],
                                    "supported_features": [1],
                                }
                            ],
                            "multiple": False,
                            "reorder": False,
                        },
                    },
                },
            }
        },
    }
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await condition.async_get_all_descriptions(hass) is new_descriptions

    # Load the light integration and check a new cache object is created
    assert await async_setup_component(hass, LIGHT_DOMAIN, {})
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_conditions", return_value=True),
    ):
        new_descriptions = await condition.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # No light conditions added, they are gated by the automation.new_triggers_conditions
    # labs flag
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await condition.async_get_all_descriptions(hass) is new_descriptions

    # Enable the new_triggers_conditions flag and verify light conditions are loaded
    assert await async_setup_component(hass, "labs", {})

    await ws_client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "automation",
            "preview_feature": "new_triggers_conditions",
            "enabled": True,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_conditions", return_value=True),
    ):
        new_descriptions = await condition.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The light conditions should now be present
    assert new_descriptions == expected_descriptions | {
        "light.is_off": {
            "fields": {},
            "target": {
                "entity": [
                    {
                        "domain": [
                            "light",
                        ],
                    },
                ],
            },
        },
        "light.is_on": {
            "fields": {},
            "target": {
                "entity": [
                    {
                        "domain": [
                            "light",
                        ],
                    },
                ],
            },
        },
        "light.is_brightness": {
            "fields": {},
            "target": {
                "entity": [
                    {
                        "domain": [
                            "light",
                        ],
                    },
                ],
            },
        },
    }

    # Verify the cache returns the same object
    assert await condition.async_get_all_descriptions(hass) is new_descriptions

    # Disable the new_triggers_conditions flag and verify light conditions are removed
    assert await async_setup_component(hass, "labs", {})

    await ws_client.send_json_auto_id(
        {
            "type": "labs/update",
            "domain": "automation",
            "preview_feature": "new_triggers_conditions",
            "enabled": False,
        }
    )

    msg = await ws_client.receive_json()
    assert msg["success"]
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_conditions", return_value=True),
    ):
        new_descriptions = await condition.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The light conditions should no longer be present
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await condition.async_get_all_descriptions(hass) is new_descriptions

    await hass.data["entity_components"][SUN_DOMAIN]._async_reset()