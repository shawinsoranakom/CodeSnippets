async def test_ssdp_encrypted_websocket_success_populates_mac_address_and_ssdp_location(
    hass: HomeAssistant,
) -> None:
    """Test starting a flow from ssdp for a supported device populates the mac."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_SSDP},
        data=MOCK_SSDP_DATA_RENDERING_CONTROL_ST,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    with patch(
        "homeassistant.components.samsungtv.config_flow.SamsungTVEncryptedWSAsyncAuthenticator",
        autospec=True,
    ) as authenticator_mock:
        authenticator_mock.return_value.try_pin.side_effect = [
            None,
            "037739871315caef138547b03e348b72",
        ]
        authenticator_mock.return_value.get_session_id_and_close.return_value = "1"

        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result2["step_id"] == "encrypted_pairing"

        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"], user_input={CONF_PIN: "invalid"}
        )
        assert result3["step_id"] == "encrypted_pairing"
        assert result3["errors"] == {"base": "invalid_pin"}

        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"], user_input={CONF_PIN: "1234"}
        )

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "TV-UE48JU6470 (UE48JU6400)"
    assert result4["data"][CONF_HOST] == "10.10.12.34"
    assert result4["data"][CONF_MAC] == "aa:bb:aa:aa:aa:aa"
    assert result4["data"][CONF_MANUFACTURER] == "Samsung Electronics"
    assert result4["data"][CONF_MODEL] == "UE48JU6400"
    assert result4["data"][CONF_PORT] == 8000
    assert (
        result4["data"][CONF_SSDP_RENDERING_CONTROL_LOCATION]
        == "http://10.10.12.34:7676/smp_15_"
    )
    assert result4["data"][CONF_TOKEN] == "037739871315caef138547b03e348b72"
    assert result4["data"][CONF_SESSION_ID] == "1"
    assert result4["result"].unique_id == "223da676-497a-4e06-9507-5e27ec4f0fb3"