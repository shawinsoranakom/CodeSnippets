async def test_setup_multiple_phonebooks(hass: HomeAssistant) -> None:
    """Test setting up manually."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_ids",
            new_callable=PropertyMock,
            return_value=[0, 1],
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.__init__",
            return_value=None,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.config_flow.FritzConnection.updatecheck",
            new_callable=PropertyMock,
            return_value=MOCK_DEVICE_INFO,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.phonebook_info",
            side_effect=[MOCK_PHONEBOOK_INFO_1, MOCK_PHONEBOOK_INFO_2],
        ),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input=MOCK_USER_DATA
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "phonebook"
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.fritzbox_callmonitor.base.FritzPhonebook.modelname",
            return_value=MOCK_PHONEBOOK_NAME_1,
        ),
        patch(
            "homeassistant.components.fritzbox_callmonitor.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PHONEBOOK: MOCK_PHONEBOOK_NAME_2},
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_PHONEBOOK_NAME_2
    assert result["data"] == {
        CONF_HOST: MOCK_HOST,
        CONF_PORT: MOCK_PORT,
        CONF_PASSWORD: MOCK_PASSWORD,
        CONF_USERNAME: MOCK_USERNAME,
        CONF_PHONEBOOK: 1,
        SERIAL_NUMBER: MOCK_SERIAL_NUMBER,
    }
    assert len(mock_setup_entry.mock_calls) == 1