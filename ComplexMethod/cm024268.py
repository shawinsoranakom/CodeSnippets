async def test_bad_certificate(
    hass: HomeAssistant,
    mqtt_mock_entry: MqttMockHAClientGenerator,
    mock_try_connection_success: MqttMockPahoClient,
    mock_ssl_context: dict[str, MagicMock],
    mock_process_uploaded_file: MagicMock,
    test_error: str | None,
    client_key_password: str,
    mock_ca_cert: bytes,
) -> None:
    """Test bad certificate tests."""

    def _side_effect_on_client_cert(data: bytes) -> MagicMock:
        """Raise on client cert only.

        The function is called twice, once for the CA chain
        and once for the client cert. We only want to raise on a client cert.
        """
        if data == MOCK_CLIENT_CERT_DER:
            raise ValueError
        mock_certificate_side_effect = MagicMock()
        mock_certificate_side_effect().public_bytes.return_value = MOCK_GENERIC_CERT
        return mock_certificate_side_effect

    # Mock certificate files
    file_id = mock_process_uploaded_file.file_id
    set_ca_cert = "custom"
    set_client_cert = True
    tls_insecure = False
    test_input = {
        mqtt.CONF_BROKER: "another-broker",
        CONF_PORT: 2345,
        mqtt.CONF_CERTIFICATE: file_id[mqtt.CONF_CERTIFICATE],
        mqtt.CONF_CLIENT_CERT: file_id[mqtt.CONF_CLIENT_CERT],
        mqtt.CONF_CLIENT_KEY: file_id[mqtt.CONF_CLIENT_KEY],
        "client_key_password": client_key_password,
        "set_ca_cert": set_ca_cert,
        "set_client_cert": True,
    }
    if test_error == "bad_certificate":
        # CA chain is not loading
        mock_ssl_context["context"]().load_verify_locations.side_effect = SSLError
        # Fail on the CA cert if DER encoded
        mock_ssl_context["load_der_x509_certificate"].side_effect = ValueError
    elif test_error == "bad_client_cert":
        # Client certificate is invalid
        mock_ssl_context["load_pem_x509_certificate"].side_effect = ValueError
        # Fail on the client cert if DER encoded
        mock_ssl_context[
            "load_der_x509_certificate"
        ].side_effect = _side_effect_on_client_cert
    elif test_error == "client_key_error":
        # Client key file is invalid
        mock_ssl_context["load_pem_private_key"].side_effect = ValueError
        mock_ssl_context["load_der_private_key"].side_effect = ValueError
    elif test_error == "bad_client_cert_key":
        # Client key file file and certificate do not pair
        mock_ssl_context["context"]().load_cert_chain.side_effect = SSLError
    elif test_error == "invalid_inclusion":
        # Client key file without client cert, client cert without key file
        test_input.pop(mqtt.CONF_CLIENT_KEY)

    mqtt_mock = await mqtt_mock_entry()
    config_entry: MockConfigEntry = hass.config_entries.async_entries(mqtt.DOMAIN)[0]
    # Add at least one advanced option to get the full form
    hass.config_entries.async_update_entry(
        config_entry,
        data={
            mqtt.CONF_BROKER: "test-broker",
            CONF_PORT: 1234,
            CONF_CLIENT_ID: "custom1234",
            mqtt.CONF_KEEPALIVE: 60,
            mqtt.CONF_TLS_INSECURE: False,
            CONF_PROTOCOL: "3.1.1",
        },
    )
    await hass.async_block_till_done()

    mqtt_mock.async_connect.reset_mock()

    result = await config_entry.start_reconfigure_flow(hass, show_advanced_options=True)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "broker"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            mqtt.CONF_BROKER: "another-broker",
            CONF_PORT: 2345,
            mqtt.CONF_KEEPALIVE: 60,
            "set_client_cert": set_client_cert,
            "set_ca_cert": set_ca_cert,
            mqtt.CONF_TLS_INSECURE: tls_insecure,
            CONF_PROTOCOL: "3.1.1",
            CONF_CLIENT_ID: "custom1234",
        },
    )
    test_input["set_client_cert"] = set_client_cert
    test_input["set_ca_cert"] = set_ca_cert
    test_input["tls_insecure"] = tls_insecure

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=test_input,
    )
    if test_error is not None:
        assert result["errors"]["base"] == test_error
        return
    assert "errors" not in result