async def test_form_user_discovery_and_password_fetch_gets_connection_refused(
    hass: HomeAssistant,
) -> None:
    """Test we can discovery and fetch the password manually."""

    mocked_roomba = _create_mocked_roomba(
        roomba_connected=True,
        master_state={"state": {"reported": {"name": "myroomba"}}},
    )

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_HOST: MOCK_IP},
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] is None
    assert result2["step_id"] == "link"

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaPassword",
        _mocked_connection_refused_on_getpassword,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.roomba.config_flow.RoombaFactory.create_roomba",
            return_value=mocked_roomba,
        ),
        patch(
            "homeassistant.components.roomba.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {CONF_PASSWORD: "password"},
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "myroomba"
    assert result4["result"].unique_id == "BLID"
    assert result4["data"] == {
        CONF_BLID: "BLID",
        CONF_CONTINUOUS: True,
        CONF_DELAY: DEFAULT_DELAY,
        CONF_HOST: MOCK_IP,
        CONF_PASSWORD: "password",
    }
    assert len(mock_setup_entry.mock_calls) == 1