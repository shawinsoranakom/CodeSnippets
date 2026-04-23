async def test_options_flow(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_api: MagicMock
) -> None:
    """Test options flow."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_api.disconnect.call_count == 0
    assert mock_api.async_connect.call_count == 1

    # Trigger options flow, first time
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    data_schema = result["data_schema"].schema
    assert set(data_schema) == {CONF_APPS, CONF_ENABLE_IME}

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_ENABLE_IME: False}
    await hass.async_block_till_done()

    assert mock_api.disconnect.call_count == 1
    assert mock_api.async_connect.call_count == 2

    # Trigger options flow, second time, no change, doesn't reload
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: False},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_ENABLE_IME: False}
    await hass.async_block_till_done()

    assert mock_api.disconnect.call_count == 1
    assert mock_api.async_connect.call_count == 2

    # Trigger options flow, third time, change, reloads
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_ENABLE_IME: True},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_ENABLE_IME: True}
    await hass.async_block_till_done()

    assert mock_api.disconnect.call_count == 2
    assert mock_api.async_connect.call_count == 3

    # test app form with new app
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APPS: APPS_NEW_ID,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "apps"
    assert result["description_placeholders"] == {
        "app_id": "",
        "example_app_id": "com.plexapp.android",
        "example_app_play_store_url": "https://play.google.com/store/apps/details?id=com.plexapp.android",
    }

    # test save value for new app
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_APP_ID: "app1",
            CONF_APP_NAME: "App1",
            CONF_APP_ICON: "Icon1",
        },
    )
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
            CONF_APP_NAME: "Application1",
            CONF_APP_ICON: "Icon1",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {
        CONF_APPS: {"app1": {CONF_APP_NAME: "Application1", CONF_APP_ICON: "Icon1"}},
        CONF_ENABLE_IME: True,
    }
    await hass.async_block_till_done()

    # test app form for delete
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
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
            CONF_APP_DELETE: True,
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert mock_config_entry.options == {CONF_ENABLE_IME: True}