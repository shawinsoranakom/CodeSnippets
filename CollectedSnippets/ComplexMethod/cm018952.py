async def test_manual_config(hass: HomeAssistant, mock_plex_calls) -> None:
    """Test creating via manual configuration."""

    class WrongCertValidaitionException(requests.exceptions.SSLError):
        """Mock the exception showing an unmatched error."""

        def __init__(self) -> None:  # pylint: disable=super-init-not-called
            self.__context__ = ssl.SSLCertVerificationError(
                "some random message that doesn't match"
            )

    # Basic mode
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["data_schema"] is None
    hass.config_entries.flow.async_abort(result["flow_id"])

    # Advanced automatic
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    assert result["data_schema"] is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_advanced"

    with patch("plexauth.PlexAuth.initiate_auth"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"setup_method": AUTOMATIC_SETUP_STRING}
        )

    assert result["type"] is FlowResultType.EXTERNAL_STEP
    hass.config_entries.flow.async_abort(result["flow_id"])

    # Advanced manual
    result = await hass.config_entries.flow.async_init(
        config_flow.DOMAIN,
        context={"source": SOURCE_USER, "show_advanced_options": True},
    )

    assert result["data_schema"] is not None
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user_advanced"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"setup_method": MANUAL_SETUP_STRING}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"

    MANUAL_SERVER = {
        CONF_HOST: MOCK_SERVERS[0][CONF_HOST],
        CONF_PORT: MOCK_SERVERS[0][CONF_PORT],
        CONF_SSL: False,
        CONF_VERIFY_SSL: True,
        CONF_TOKEN: MOCK_TOKEN,
    }

    MANUAL_SERVER_NO_HOST_OR_TOKEN = {
        CONF_PORT: MOCK_SERVERS[0][CONF_PORT],
        CONF_SSL: False,
        CONF_VERIFY_SSL: True,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=MANUAL_SERVER_NO_HOST_OR_TOKEN
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"
    assert result["errors"]["base"] == "host_or_token"

    with patch(
        "plexapi.server.PlexServer",
        side_effect=requests.exceptions.SSLError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MANUAL_SERVER
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"
    assert result["errors"]["base"] == "ssl_error"

    with patch(
        "plexapi.server.PlexServer",
        side_effect=WrongCertValidaitionException,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MANUAL_SERVER
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"
    assert result["errors"]["base"] == "ssl_error"

    with patch(
        "homeassistant.components.plex.PlexServer.connect",
        side_effect=requests.exceptions.SSLError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MANUAL_SERVER
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_setup"
    assert result["errors"]["base"] == "ssl_error"

    with (
        patch("homeassistant.components.plex.PlexWebsocket", autospec=True),
        patch("homeassistant.components.plex.GDM", return_value=MockGDM(disabled=True)),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MANUAL_SERVER
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert result["title"] == "http://1.2.3.4:32400"
    assert result["data"][CONF_SERVER] == "Plex Server 1"
    assert result["data"][CONF_SERVER_IDENTIFIER] == "unique_id_123"
    assert result["data"][PLEX_SERVER_CONFIG][CONF_URL] == "http://1.2.3.4:32400"
    assert result["data"][PLEX_SERVER_CONFIG][CONF_TOKEN] == MOCK_TOKEN