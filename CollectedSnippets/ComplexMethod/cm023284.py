async def test_intent_recommended_user(
    hass: HomeAssistant,
    install_addon: AsyncMock,
    start_addon: AsyncMock,
    set_addon_options: AsyncMock,
) -> None:
    """Test the intent_recommended step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_recommended"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "install_addon"

    # Make sure the flow continues when the progress task is done.
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert install_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_addon_user"
    data_schema = result["data_schema"]
    assert data_schema is not None
    assert len(data_schema.schema) == 2
    assert data_schema.schema.get(CONF_USB_PATH) is not None
    assert data_schema.schema.get(CONF_SOCKET_PATH) is not None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_USB_PATH: "/test",
        },
    )

    assert set_addon_options.call_args == call(
        "core_zwave_js",
        AddonsOptions(
            config={
                CONF_ADDON_DEVICE: "/test",
                CONF_ADDON_S0_LEGACY_KEY: "",
                CONF_ADDON_S2_ACCESS_CONTROL_KEY: "",
                CONF_ADDON_S2_AUTHENTICATED_KEY: "",
                CONF_ADDON_S2_UNAUTHENTICATED_KEY: "",
                CONF_ADDON_LR_S2_ACCESS_CONTROL_KEY: "",
                CONF_ADDON_LR_S2_AUTHENTICATED_KEY: "",
            }
        ),
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "start_addon"

    with (
        patch(
            "homeassistant.components.zwave_js.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.zwave_js.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    assert start_addon.call_args == call("core_zwave_js")

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://host1:3001",
        "usb_path": "/test",
        "socket_path": None,
        "s0_legacy_key": "",
        "s2_access_control_key": "",
        "s2_authenticated_key": "",
        "s2_unauthenticated_key": "",
        "lr_s2_access_control_key": "",
        "lr_s2_authenticated_key": "",
        "use_addon": True,
        "integration_created_addon": True,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1