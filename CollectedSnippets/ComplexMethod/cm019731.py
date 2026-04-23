async def test_flow_reauth_no_username_or_device(
    hass: HomeAssistant,
    get_devices: dict[str, Any],
    get_me: dict[str, Any],
    p_error: str,
    mock_client: MagicMock,
    get_data: tuple[SensiboData, dict[str, Any], dict[str, Any]],
) -> None:
    """Test reauth flow with errors from api."""
    entry = MockConfigEntry(
        version=2,
        domain=DOMAIN,
        unique_id="firstnamelastname",
        data={CONF_API_KEY: "1234567890"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_client.async_get_devices.return_value = get_devices
    mock_client.async_get_me.return_value = get_me

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_API_KEY: "1234567890",
        },
    )

    assert result["step_id"] == "reauth_confirm"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": p_error}

    mock_client.async_get_devices.return_value = get_data[2]
    mock_client.async_get_me.return_value = get_data[1]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "1234567890"},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {CONF_API_KEY: "1234567890"}