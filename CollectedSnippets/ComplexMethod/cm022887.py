async def test_reauth(hass: HomeAssistant) -> None:
    """Test we can reauth."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_USERNAME: "bob",
            CONF_HOST: f"http://{MOCK_HOSTNAME}:1443{ISY_URL_POSTFIX}",
        },
        unique_id=MOCK_UUID,
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    with patch(
        PATCH_CONNECTION,
        side_effect=ISYInvalidAuthError(),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"password": "invalid_auth"}

    with patch(
        PATCH_CONNECTION,
        side_effect=ISYConnectionError(),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )

    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] == {"base": "cannot_connect"}

    with (
        patch(PATCH_CONNECTION, return_value=MOCK_CONFIG_RESPONSE),
        patch(
            "homeassistant.components.isy994.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {
                CONF_USERNAME: "test-username",
                CONF_PASSWORD: "test-password",
            },
        )
        await hass.async_block_till_done()

    assert mock_setup_entry.called
    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "reauth_successful"