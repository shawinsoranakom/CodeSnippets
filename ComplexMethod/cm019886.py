async def test_reauth_flow_preserves_ssl_when_omitted(
    hass: HomeAssistant,
) -> None:
    """Test reauth preserves existing SSL value when key is omitted from input."""
    ssl_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_INSTALLATION_ID,
        data={
            CONF_HOST: MOCK_HOST,
            CONF_PORT: DEFAULT_PORT,
            CONF_USERNAME: "old-user",
            CONF_PASSWORD: "old-pass",
            CONF_SSL: True,
            CONF_INSTALLATION_ID: MOCK_INSTALLATION_ID,
            CONF_MODEL: MOCK_MODEL,
            CONF_SERIAL: MOCK_SERIAL,
        },
        title=f"Victron OS {MOCK_INSTALLATION_ID} ({MOCK_HOST}:{DEFAULT_PORT})",
    )
    ssl_entry.add_to_hass(hass)
    result = await ssl_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "new-user",
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert ssl_entry.data[CONF_USERNAME] == "new-user"
    assert ssl_entry.data[CONF_PASSWORD] == "new-password"
    assert ssl_entry.data[CONF_SSL] is True