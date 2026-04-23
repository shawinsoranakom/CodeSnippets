async def test_bridge_connection_failed(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that connection errors to the bridge are handled."""
    create_mock_api_discovery(aioclient_mock, [])

    with patch(
        "homeassistant.components.hue.config_flow.discover_bridge",
        side_effect=ClientError,
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"host": "blah"}
        )

        # a warning message should have been logged that the bridge could not be reached
        assert "Error while attempting to retrieve discovery information" in caplog.text

        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

        # test again with zeroconf discovered wrong bridge IP
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN,
            context={"source": config_entries.SOURCE_ZEROCONF},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("1.2.3.4"),
                ip_addresses=[ip_address("1.2.3.4")],
                port=443,
                hostname="Philips-hue.local",
                type="_hue._tcp.local.",
                name="Philips Hue - ABCABC._hue._tcp.local.",
                properties={
                    "_raw": {"bridgeid": b"ecb5fafffeabcabc", "modelid": b"BSB002"},
                    "bridgeid": "ecb5fafffeabcabc",
                    "modelid": "BSB002",
                },
            ),
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

        # test again with homekit discovered wrong bridge IP
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN,
            context={"source": config_entries.SOURCE_HOMEKIT},
            data=ZeroconfServiceInfo(
                ip_address=ip_address("0.0.0.0"),
                ip_addresses=[ip_address("0.0.0.0")],
                hostname="mock_hostname",
                name="mock_name",
                port=None,
                properties={ATTR_PROPERTIES_ID: "aa:bb:cc:dd:ee:ff"},
                type="mock_type",
            ),
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"

        # repeat test with import flow
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data={"host": "blah"},
        )
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "cannot_connect"