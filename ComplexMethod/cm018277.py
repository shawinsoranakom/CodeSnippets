async def test_reconfigure_not_successful(
    hass: HomeAssistant,
    fc_class_mock,
) -> None:
    """Test starting a reconfigure flow but no connection found."""

    mock_config = MockConfigEntry(domain=DOMAIN, data=MOCK_USER_DATA)
    mock_config.add_to_hass(hass)

    with (
        patch(
            "homeassistant.components.fritz.config_flow.FritzConnection",
            side_effect=[FritzConnectionException, fc_class_mock],
        ),
        patch(
            "homeassistant.components.fritz.coordinator.FritzBoxTools._update_device_info",
            return_value=MOCK_FIRMWARE_INFO,
        ),
        patch(
            "homeassistant.components.fritz.async_setup_entry",
        ),
        patch(
            "requests.get",
        ) as mock_request_get,
        patch(
            "requests.post",
        ) as mock_request_post,
    ):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.content = MOCK_REQUEST
        mock_request_post.return_value.status_code = 200
        mock_request_post.return_value.text = MOCK_REQUEST

        result = await mock_config.start_reconfigure_flow(hass)

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "fake_host",
                CONF_SSL: False,
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reconfigure"
        assert result["errors"]["base"] == ERROR_CANNOT_CONNECT

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "fake_host",
                CONF_SSL: False,
            },
        )

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reconfigure_successful"
        assert mock_config.data == {
            CONF_HOST: "fake_host",
            CONF_PASSWORD: "fake_pass",
            CONF_USERNAME: "fake_user",
            CONF_PORT: 49000,
            CONF_SSL: False,
        }