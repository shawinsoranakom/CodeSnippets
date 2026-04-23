async def test_reauth(hass: HomeAssistant) -> None:
    """Test we get the form."""

    mock_config = MockConfigEntry(
        domain=DOMAIN,
        unique_id="test-mac",
        data={
            "host": "1.1.1.1",
            "hostname": "test-mac",
            "ssl_certificate": "test-cert.pem",
            "ssl_key": "test-key.pem",
        },
        title="shc012345",
    )
    mock_config.add_to_hass(hass)
    result = await mock_config.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

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
            {"host": "2.2.2.2"},
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
        patch("boschshcpy.session.SHCSession.authenticate"),
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

    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"

    assert mock_config.data["host"] == "2.2.2.2"

    assert len(mock_setup_entry.mock_calls) == 1