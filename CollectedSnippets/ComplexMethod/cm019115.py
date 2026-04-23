async def test_options_flow(hass: HomeAssistant) -> None:
    """Test config flow options."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data=CONFIG_ADB_SERVER,
        unique_id=ETH_MAC,
        options={
            CONF_APPS: {"app1": "App1"},
            CONF_STATE_DETECTION_RULES: {"com.plexapp.android": VALID_DETECT_RULE},
        },
    )
    config_entry.add_to_hass(hass)

    with PATCH_SETUP_ENTRY:
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(config_entry.entry_id)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test app form with existing app
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: "app1",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "apps"

        # test change value in apps form
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_NAME: "Appl1",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test app form with new app
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: APPS_NEW_ID,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "apps"

        # test save value for new app
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_ID: "app2",
                CONF_APP_NAME: "Appl2",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test app form for delete
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APPS: "app1",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "apps"

        # test delete app1
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_APP_NAME: "Appl1",
                CONF_APP_DELETE: True,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test rules form with existing rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: "com.plexapp.android",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "rules"

        # test change value in rule form with invalid json rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: "a",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "rules"
        assert result["errors"] == {"base": "invalid_det_rules"}

        # test change value in rule form with invalid rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: {"a": "b"},
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "rules"
        assert result["errors"] == {"base": "invalid_det_rules"}

        # test change value in rule form with valid rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_VALUES: ["standby"],
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test rule form with new rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: RULES_NEW_ID,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "rules"

        # test save value for new rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_ID: "rule2",
                CONF_RULE_VALUES: VALID_DETECT_RULE,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        # test rules form with delete existing rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_STATE_DETECTION_RULES: "com.plexapp.android",
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "rules"

        # test delete rule
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_RULE_DELETE: True,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "init"

        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_GET_SOURCES: True,
                CONF_EXCLUDE_UNNAMED_APPS: True,
                CONF_SCREENCAP_INTERVAL: 1,
                CONF_TURN_OFF_COMMAND: "off",
                CONF_TURN_ON_COMMAND: "on",
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY

        apps_options = config_entry.options[CONF_APPS]
        assert apps_options.get("app1") is None
        assert apps_options["app2"] == "Appl2"

        assert config_entry.options[CONF_GET_SOURCES] is True
        assert config_entry.options[CONF_EXCLUDE_UNNAMED_APPS] is True
        assert config_entry.options[CONF_SCREENCAP_INTERVAL] == 1
        assert config_entry.options[CONF_TURN_OFF_COMMAND] == "off"
        assert config_entry.options[CONF_TURN_ON_COMMAND] == "on"