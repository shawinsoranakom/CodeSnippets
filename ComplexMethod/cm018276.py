async def test_user(
    hass: HomeAssistant,
    fc_class_mock,
    show_advanced_options: bool,
    user_input: dict,
    expected_config: dict,
    expected_options: dict,
) -> None:
    """Test starting a flow by user."""
    with (
        patch(
            "homeassistant.components.fritz.config_flow.FritzConnection",
            side_effect=fc_class_mock,
        ),
        patch(
            "homeassistant.components.fritz.coordinator.FritzBoxTools._update_device_info",
            return_value=MOCK_FIRMWARE_INFO,
        ),
        patch("homeassistant.components.fritz.async_setup_entry") as mock_setup_entry,
        patch(
            "requests.get",
        ) as mock_request_get,
        patch(
            "requests.post",
        ) as mock_request_post,
        patch(
            "homeassistant.components.fritz.config_flow.socket.gethostbyname",
            return_value=MOCK_IPS["fritz.box"],
        ),
    ):
        mock_request_get.return_value.status_code = 200
        mock_request_get.return_value.content = MOCK_REQUEST
        mock_request_post.return_value.status_code = 200
        mock_request_post.return_value.text = MOCK_REQUEST

        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                "source": SOURCE_USER,
                "show_advanced_options": show_advanced_options,
            },
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=user_input
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["data"] == expected_config
        assert result["options"] == expected_options
        assert not result["result"].unique_id

    assert mock_setup_entry.called