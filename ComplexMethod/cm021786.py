async def test_setup_with_apps_additional_apps_config(
    hass: HomeAssistant,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test device setup with apps and apps["additional_configs"] in config."""
    config_entry = MockConfigEntry(
        domain=DOMAIN, data=MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG, unique_id=UNIQUE_ID
    )
    async with _cm_for_test_setup_tv_with_apps(
        hass,
        config_entry,
        ADDITIONAL_APP_CONFIG["config"],
    ):
        attr = hass.states.get(ENTITY_ID).attributes
        assert attr[ATTR_INPUT_SOURCE_LIST].count(CURRENT_APP) == 1
        _assert_source_list_with_apps(
            list(
                INPUT_LIST_WITH_APPS
                + APP_NAME_LIST
                + [
                    app["name"]
                    for app in MOCK_TV_WITH_ADDITIONAL_APPS_CONFIG[CONF_APPS][
                        CONF_ADDITIONAL_CONFIGS
                    ]
                    if app["name"] not in APP_NAME_LIST
                ]
            ),
            attr,
        )
        assert ADDITIONAL_APP_CONFIG["name"] in attr[ATTR_INPUT_SOURCE_LIST]
        assert attr[ATTR_INPUT_SOURCE] == ADDITIONAL_APP_CONFIG["name"]
        assert attr["app_name"] == ADDITIONAL_APP_CONFIG["name"]
        assert "app_id" not in attr

    await _test_service(
        hass,
        MP_DOMAIN,
        "launch_app",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: "Netflix"},
        "Netflix",
        APP_LIST,
    )
    await _test_service(
        hass,
        MP_DOMAIN,
        "launch_app_config",
        SERVICE_SELECT_SOURCE,
        {ATTR_INPUT_SOURCE: CURRENT_APP},
        **CUSTOM_CONFIG,
    )

    # Test that invalid app does nothing
    with (
        patch("homeassistant.components.vizio.VizioAsync.launch_app") as service_call1,
        patch(
            "homeassistant.components.vizio.VizioAsync.launch_app_config"
        ) as service_call2,
    ):
        await hass.services.async_call(
            MP_DOMAIN,
            SERVICE_SELECT_SOURCE,
            service_data={ATTR_ENTITY_ID: ENTITY_ID, ATTR_INPUT_SOURCE: "_"},
            blocking=True,
        )
        assert not service_call1.called
        assert not service_call2.called