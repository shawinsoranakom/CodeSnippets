async def test_user_with_filestation(
    hass: HomeAssistant,
    service_with_filestation: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test user config."""
    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service_with_filestation,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=None
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service_with_filestation,
    ):
        # test with all provided
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: HOST,
                CONF_PORT: PORT,
                CONF_SSL: USE_SSL,
                CONF_VERIFY_SSL: VERIFY_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "backup_share"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_BACKUP_SHARE: "/ha_backup", CONF_BACKUP_PATH: "automatic_ha_backups"},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == HOST
    assert result["data"] == snapshot