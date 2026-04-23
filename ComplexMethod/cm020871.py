async def test_zeroconf_confirm_with_password_success(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_homevolt_client: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test zeroconf confirm collects password and creates entry when auth is required."""

    mock_homevolt_client.update_info.side_effect = HomevoltAuthenticationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=DISCOVERY_INFO,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"] == {"host": "192.168.1.123"}

    mock_homevolt_client.update_info.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "test-password"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Homevolt"
    assert result["data"] == {
        CONF_HOST: "192.168.1.123",
        CONF_PASSWORD: "test-password",
    }
    assert result["result"].unique_id == "40580137858664"
    assert len(mock_setup_entry.mock_calls) == 1