async def test_reauth(hass: HomeAssistant, user, cloud_devices) -> None:
    """Test reauth flow."""
    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CLOUD_UNIQUE_ID,
        data={**CLOUD_CONFIG, CONF_ACCESS_TOKEN: "blah"},
    )
    mock_config.add_to_hass(hass)

    result = await mock_config.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {}

    with patch("python_awair.AwairClient.query", side_effect=AuthError()):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ACCESS_TOKEN: "bad"},
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {CONF_ACCESS_TOKEN: "invalid_access_token"}

    with (
        patch(
            "python_awair.AwairClient.query",
            side_effect=[user, cloud_devices],
        ),
        patch(
            "homeassistant.components.awair.async_setup_entry", return_value=True
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_ACCESS_TOKEN: "good"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    mock_setup_entry.assert_called_once()
    assert dict(mock_config.data) == {CONF_ACCESS_TOKEN: "good"}