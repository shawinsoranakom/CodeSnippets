async def test_form(hass: HomeAssistant) -> None:
    """Test that the form is served with valid input."""

    with (
        patch(
            "homeassistant.components.qnap_qsw.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_live",
            return_value=LIVE_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.get_system_board",
            return_value=SYSTEM_BOARD_MOCK,
        ),
        patch(
            "homeassistant.components.qnap_qsw.QnapQswApi.post_users_login",
            return_value=USERS_LOGIN_MOCK,
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )

        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], CONFIG
        )

        await hass.async_block_till_done()

        conf_entries = hass.config_entries.async_entries(DOMAIN)
        entry = conf_entries[0]
        assert entry.state is ConfigEntryState.LOADED

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert (
            result["title"]
            == f"QNAP {SYSTEM_BOARD_MOCK[API_RESULT][API_PRODUCT]} {SYSTEM_BOARD_MOCK[API_RESULT][API_MAC_ADDR]}"
        )
        assert result["data"][CONF_URL] == CONFIG[CONF_URL]
        assert result["data"][CONF_USERNAME] == CONFIG[CONF_USERNAME]
        assert result["data"][CONF_PASSWORD] == CONFIG[CONF_PASSWORD]

        assert len(mock_setup_entry.mock_calls) == 1