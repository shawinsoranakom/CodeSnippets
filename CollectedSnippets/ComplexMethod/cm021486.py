async def test_form_user_discovery_not_devices_found_and_password_fetch_fails_and_cannot_connect(
    hass: HomeAssistant,
) -> None:
    """Test discovery finds no devices and password fetch fails then we cannot connect."""

    mocked_roomba = _create_mocked_roomba(
        connect=RoombaConnectionError,
        roomba_connected=True,
        master_state={"state": {"reported": {"name": "myroomba"}}},
    )

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery",
        _mocked_no_devices_found_discovery,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "manual"

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: MOCK_IP},
        )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] is None

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaPassword",
        _mocked_failed_getpassword,
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

    assert result4["type"] is FlowResultType.FORM
    assert result4["errors"] == {"base": "cannot_connect"}
    assert len(mock_setup_entry.mock_calls) == 0