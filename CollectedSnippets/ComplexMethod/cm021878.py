async def test_flow_works(hass: HomeAssistant, simple_mock_home) -> None:
    """Test config flow."""

    with (
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
            return_value=False,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.get_auth",
            return_value=True,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=DEFAULT_CONFIG,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"
    assert result["errors"] == {"base": "press_the_button"}

    flow = next(
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "ABC123"

    with (
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_checkbutton",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_setup",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipAuth.async_register",
            return_value=True,
        ),
        patch(
            "homeassistant.components.homematicip_cloud.hap.HomematicipHAP.async_connect",
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ABC123"
    assert result["data"] == {"hapid": "ABC123", "authtoken": True, "name": "hmip"}
    assert result["result"].unique_id == "ABC123"