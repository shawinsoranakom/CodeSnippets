async def test_full_ssdp_flow_implementation(hass: HomeAssistant) -> None:
    """Test the full SSDP flow from start to finish."""

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO_P_B)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"
    assert result["description_placeholders"] == {
        CONF_NAME: f"WL{WILIGHT_ID}",
        "components": "light",
    }

    with patch("homeassistant.components.wilight.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"WL{WILIGHT_ID}"

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_SERIAL_NUMBER] == UPNP_SERIAL
    assert result["data"][CONF_MODEL_NAME] == UPNP_MODEL_NAME_P_B