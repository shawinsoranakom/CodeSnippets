async def test_manual_flow_detects_failed_user_authorization(
    hass: HomeAssistant,
    mock_homewizardenergy_v2: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test config flow accepts user configuration and detects failed button press by user."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Simulate v2 support but not authorized
    mock_homewizardenergy_v2.device.side_effect = UnauthorizedError
    mock_homewizardenergy_v2.get_token.side_effect = DisabledError

    with patch(
        "homeassistant.components.homewizard.config_flow.has_v2_api", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_IP_ADDRESS: "2.2.2.2"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authorize"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "authorize"
    assert result["errors"] == {"base": "authorization_failed"}

    # Restore normal functionality
    mock_homewizardenergy_v2.device.side_effect = None
    mock_homewizardenergy_v2.get_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup_entry.mock_calls) == 1