async def test_form_reauth_encrypted(hass: HomeAssistant) -> None:
    """Test reauth flow for encrypted TVs."""
    encrypted_entry_data = deepcopy(ENTRYDATA_ENCRYPTED_WEBSOCKET)
    del encrypted_entry_data[CONF_TOKEN]
    del encrypted_entry_data[CONF_SESSION_ID]

    entry = MockConfigEntry(domain=DOMAIN, data=encrypted_entry_data)
    entry.add_to_hass(hass)
    assert entry.state is ConfigEntryState.NOT_LOADED

    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.samsungtv.config_flow.SamsungTVEncryptedWSAsyncAuthenticator",
        autospec=True,
    ) as authenticator_mock:
        authenticator_mock.return_value.try_pin.side_effect = [
            None,
            "037739871315caef138547b03e348b72",
        ]
        authenticator_mock.return_value.get_session_id_and_close.return_value = "1"

        result = await hass.config_entries.flow.async_configure(result["flow_id"])

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm"
        assert result["errors"] == {}

        # First time on reauth_confirm_encrypted
        # creates the authenticator, start pairing and requests PIN
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm_encrypted"

        # Invalid PIN
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "invalid"}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "reauth_confirm_encrypted"

        # Valid PIN
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_PIN: "1234"}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.ABORT
        assert result["reason"] == "reauth_successful"
        assert entry.state is ConfigEntryState.LOADED

    authenticator_mock.assert_called_once()
    assert authenticator_mock.call_args[0] == ("10.10.12.34",)

    authenticator_mock.return_value.start_pairing.assert_called_once()
    assert authenticator_mock.return_value.try_pin.call_count == 2
    assert authenticator_mock.return_value.try_pin.call_args_list == [
        call("invalid"),
        call("1234"),
    ]
    authenticator_mock.return_value.get_session_id_and_close.assert_called_once()

    assert entry.data[CONF_TOKEN] == "037739871315caef138547b03e348b72"
    assert entry.data[CONF_SESSION_ID] == "1"