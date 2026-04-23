async def test_form_user(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with (
        patch(
            "boschshcpy.session.SHCSession.mdns_info",
            return_value=SHCInformation,
        ),
        patch(
            "boschshcpy.information.SHCInformation.name",
            new_callable=PropertyMock,
            return_value="shc012345",
        ),
        patch(
            "boschshcpy.information.SHCInformation.unique_id",
            new_callable=PropertyMock,
            return_value="test-mac",
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "credentials"
    assert result2["errors"] == {}

    with (
        patch(
            "boschshcpy.register_client.SHCRegisterClient.register",
            return_value={
                "token": "abc:123",
                "cert": b"content_cert",
                "key": b"content_key",
            },
        ),
        patch("os.mkdir"),
        patch("homeassistant.components.bosch_shc.config_flow.open"),
        patch("boschshcpy.session.SHCSession.authenticate") as mock_authenticate,
        patch(
            "homeassistant.components.bosch_shc.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {"password": "test"},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "shc012345"
    assert result3["data"] == {
        "host": "1.1.1.1",
        "ssl_certificate": hass.config.path(DOMAIN, "test-mac", CONF_SHC_CERT),
        "ssl_key": hass.config.path(DOMAIN, "test-mac", CONF_SHC_KEY),
        "token": "abc:123",
        "hostname": "123",
    }

    assert len(mock_authenticate.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1