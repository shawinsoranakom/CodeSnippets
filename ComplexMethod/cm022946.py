async def test_script_variables(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test defining scripts."""
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "script1": {
                    "variables": {
                        "this_variable": "{{this.entity_id}}",
                        "test_var": "from_config",
                        "templated_config_var": "{{ var_from_service | default('config-default') }}",
                    },
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                                "templated_config_var": "{{ templated_config_var }}",
                                "this_template": "{{this.entity_id}}",
                                "this_variable": "{{this_variable}}",
                            },
                        },
                    ],
                },
                "script2": {
                    "variables": {
                        "test_var": "from_config",
                    },
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                            },
                        },
                    ],
                },
                "script3": {
                    "variables": {
                        "test_var": "{{ break + 1 }}",
                    },
                    "sequence": [
                        {
                            "action": "test.script",
                            "data": {
                                "value": "{{ test_var }}",
                            },
                        },
                    ],
                },
            }
        },
    )

    mock_calls = async_mock_service(hass, "test", "script")

    await hass.services.async_call(
        "script", "script1", {"var_from_service": "hello"}, blocking=True
    )

    assert len(mock_calls) == 1
    assert mock_calls[0].data["value"] == "from_config"
    assert mock_calls[0].data["templated_config_var"] == "hello"
    # Verify this available to all templates
    assert mock_calls[0].data.get("this_template") == "script.script1"
    # Verify this available during trigger variables rendering
    assert mock_calls[0].data.get("this_variable") == "script.script1"

    await hass.services.async_call(
        "script", "script1", {"test_var": "from_service"}, blocking=True
    )

    assert len(mock_calls) == 2
    assert mock_calls[1].data["value"] == "from_service"
    assert mock_calls[1].data["templated_config_var"] == "config-default"

    # Call script with vars but no templates in it
    await hass.services.async_call(
        "script", "script2", {"test_var": "from_service"}, blocking=True
    )

    assert len(mock_calls) == 3
    assert mock_calls[2].data["value"] == "from_service"

    assert "Error rendering variables" not in caplog.text
    with pytest.raises(TemplateError):
        await hass.services.async_call("script", "script3", blocking=True)
    assert "Error rendering variables" in caplog.text
    assert len(mock_calls) == 3

    await hass.services.async_call("script", "script3", {"break": 0}, blocking=True)

    assert len(mock_calls) == 4
    assert mock_calls[3].data["value"] == 1