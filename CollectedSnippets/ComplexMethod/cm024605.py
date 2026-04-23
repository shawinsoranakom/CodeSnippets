async def test_user(
    hass: HomeAssistant,
    service: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test user config."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=None
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service,
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
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL
    assert result["title"] == HOST
    assert result["data"] == snapshot

    service.information.serial = SERIAL_2
    with patch(
        "homeassistant.components.synology_dsm.config_flow.SynologyDSM",
        return_value=service,
    ):
        # test without port + False SSL
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
            data={
                CONF_HOST: HOST,
                CONF_SSL: False,
                CONF_VERIFY_SSL: VERIFY_SSL,
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == SERIAL_2
    assert result["title"] == HOST
    assert result["data"] == snapshot