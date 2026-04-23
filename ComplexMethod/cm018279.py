async def test_upnp_not_enabled(hass: HomeAssistant) -> None:
    """Test if UPNP service is enabled on the router."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Disable UPnP
    services = deepcopy(MOCK_FB_SERVICES)
    services["X_AVM-DE_UPnP1"]["GetInfo"]["NewEnable"] = False

    with patch(
        "homeassistant.components.fritz.config_flow.FritzConnection",
        return_value=FritzConnectionMock(services),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT_SIMPLE
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"]["base"] == ERROR_UPNP_NOT_CONFIGURED

    # Enable UPnP
    services["X_AVM-DE_UPnP1"]["GetInfo"]["NewEnable"] = True

    with (
        patch(
            "homeassistant.components.fritz.config_flow.FritzConnection",
            return_value=FritzConnectionMock(services),
        ),
        patch(
            "homeassistant.components.fritz.config_flow.socket.gethostbyname",
            return_value=MOCK_IPS["fritz.box"],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_INPUT_SIMPLE
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == "fake_host"
        assert result["data"][CONF_PASSWORD] == "fake_pass"
        assert result["data"][CONF_USERNAME] == "fake_user"
        assert result["data"][CONF_PORT] == 49000
        assert result["data"][CONF_SSL] is False