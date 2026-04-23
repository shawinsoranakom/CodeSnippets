async def test_clean_discovery_on_user_create(
    hass: HomeAssistant,
    supervisor,
    addon_running,
    addon_options,
) -> None:
    """Test discovery flow is cleaned up when a user flow is finished."""

    addon_options["device"] = "/test"
    addon_options["s0_legacy_key"] = "new123"
    addon_options["s2_access_control_key"] = "new456"
    addon_options["s2_authenticated_key"] = "new789"
    addon_options["s2_unauthenticated_key"] = "new987"
    addon_options["lr_s2_access_control_key"] = "new654"
    addon_options["lr_s2_authenticated_key"] = "new321"

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_HASSIO},
        data=HassioServiceInfo(
            config=ADDON_DISCOVERY_INFO,
            name="Z-Wave JS",
            slug=ADDON_SLUG,
            uuid="1234",
        ),
    )

    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "installation_type"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "intent_custom"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "on_supervisor"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"use_addon": False}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    with (
        patch(
            "homeassistant.components.zwave_js.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.zwave_js.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "url": "ws://localhost:3000",
            },
        )
        await hass.async_block_till_done()

    assert len(hass.config_entries.flow.async_progress()) == 0
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TITLE
    assert result["data"] == {
        "url": "ws://localhost:3000",
        "usb_path": None,
        "socket_path": None,
        "s0_legacy_key": None,
        "s2_access_control_key": None,
        "s2_authenticated_key": None,
        "s2_unauthenticated_key": None,
        "lr_s2_access_control_key": None,
        "lr_s2_authenticated_key": None,
        "use_addon": False,
        "integration_created_addon": False,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1