async def test_form_create_entry_with_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test that the user step with auth works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.nam.NettigoAirMonitor.async_get_mac_address",
        side_effect=[AuthFailedError("Authorization has failed"), "aa:bb:cc:dd:ee:ff"],
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "credentials"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_AUTH,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.10.2.3"
    assert result["data"]["host"] == "10.10.2.3"
    assert result["data"]["username"] == "fake_username"
    assert result["data"]["password"] == "fake_password"
    assert len(mock_setup_entry.mock_calls) == 1