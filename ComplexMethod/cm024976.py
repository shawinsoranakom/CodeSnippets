async def test_async_get_all_descriptions(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    sun_trigger_descriptions: str,
) -> None:
    """Test async_get_all_descriptions."""
    tag_trigger_descriptions = """
        _:
          target:
            entity:
              domain: alarm_control_panel
        """
    text_trigger_descriptions = """
        changed:
          target:
            entity:
              domain: text
        """

    ws_client = await hass_ws_client(hass)

    assert await async_setup_component(hass, SUN_DOMAIN, {})
    assert await async_setup_component(hass, SYSTEM_HEALTH_DOMAIN, {})
    await hass.async_block_till_done()

    def _load_yaml(fname, secrets=None):
        if fname.endswith("sun/triggers.yaml"):
            trigger_descriptions = sun_trigger_descriptions
        elif fname.endswith("tag/triggers.yaml"):
            trigger_descriptions = tag_trigger_descriptions
        elif fname.endswith("text/triggers.yaml"):
            trigger_descriptions = text_trigger_descriptions
        with io.StringIO(trigger_descriptions) as file:
            return parse_yaml(file)

    with (
        patch(
            "homeassistant.helpers.trigger._load_triggers_files",
            side_effect=trigger._load_triggers_files,
        ) as proxy_load_triggers_files,
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_triggers", return_value=True),
    ):
        descriptions = await trigger.async_get_all_descriptions(hass)

    # Test we only load triggers.yaml for integrations with triggers,
    # system_health has no triggers
    assert proxy_load_triggers_files.mock_calls[0][1][0] == unordered(
        [
            await async_get_integration(hass, SUN_DOMAIN),
        ]
    )

    # system_health does not have triggers and should not be in descriptions
    expected_descriptions = {
        "sun": {
            "fields": {
                "event": {
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
                "offset": {"selector": {"time": {}}},
            }
        }
    }

    assert descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await trigger.async_get_all_descriptions(hass) is descriptions

    # Load the tag integration and check a new cache object is created
    assert await async_setup_component(hass, TAG_DOMAIN, {})
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_triggers", return_value=True),
    ):
        new_descriptions = await trigger.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The tag trigger should now be present
    expected_descriptions |= {
        "tag": {
            "target": {
                "entity": [
                    {
                        "domain": ["alarm_control_panel"],
                    }
                ],
            },
            "fields": {},
        },
    }
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await trigger.async_get_all_descriptions(hass) is new_descriptions

    # Load the text integration and check a new cache object is created
    assert await async_setup_component(hass, TEXT_DOMAIN, {})
    await hass.async_block_till_done()

    with (
        patch(
            "annotatedyaml.loader.load_yaml",
            side_effect=_load_yaml,
        ),
        patch.object(Integration, "has_triggers", return_value=True),
    ):
        new_descriptions = await trigger.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # No text triggers added, they are gated by the automation.new_triggers_conditions
    # labs flag
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await trigger.async_get_all_descriptions(hass) is new_descriptions

    # Enable the new_triggers_conditions flag and verify text triggers are loaded
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
        patch.object(Integration, "has_triggers", return_value=True),
    ):
        new_descriptions = await trigger.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The text triggers should now be present
    assert new_descriptions == expected_descriptions | {
        "text.changed": {
            "fields": {},
            "target": {
                "entity": [
                    {
                        "domain": [
                            "text",
                        ],
                    },
                ],
            },
        },
    }

    # Verify the cache returns the same object
    assert await trigger.async_get_all_descriptions(hass) is new_descriptions

    # Disable the new_triggers_conditions flag and verify text triggers are removed
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
        patch.object(Integration, "has_triggers", return_value=True),
    ):
        new_descriptions = await trigger.async_get_all_descriptions(hass)
    assert new_descriptions is not descriptions
    # The text triggers should no longer be present
    assert new_descriptions == expected_descriptions

    # Verify the cache returns the same object
    assert await trigger.async_get_all_descriptions(hass) is new_descriptions

    await hass.data["entity_components"][SUN_DOMAIN]._async_reset()