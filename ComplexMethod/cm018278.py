async def test_ssdp(hass: HomeAssistant, fc_class_mock) -> None:
    """Test starting a flow from discovery."""
    with (
        patch(
            "homeassistant.components.fritz.config_flow.FritzConnection",
            side_effect=fc_class_mock,
        ),
        patch(
            "homeassistant.components.fritz.coordinator.FritzBoxTools._update_device_info",
            return_value=MOCK_FIRMWARE_INFO,
        ),
        patch(
            "homeassistant.components.fritz.config_flow.socket.gethostbyname",
            return_value=MOCK_IPS["fritz.box"],
        ),
        patch("homeassistant.components.fritz.async_setup_entry") as mock_setup_entry,
        patch("requests.get") as mock_request_get,
        patch("requests.post") as mock_request_post,
    ):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.content = MOCK_REQUEST
        mock_request_post.return_value.status_code = 200
        mock_request_post.return_value.text = MOCK_REQUEST

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_SSDP}, data=MOCK_SSDP_DATA
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "confirm"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_USERNAME: "fake_user",
                CONF_PASSWORD: "fake_pass",
            },
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_HOST] == MOCK_IPS["fritz.box"]
        assert result["data"][CONF_PASSWORD] == "fake_pass"
        assert result["data"][CONF_USERNAME] == "fake_user"

    assert mock_setup_entry.called