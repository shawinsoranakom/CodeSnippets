async def test_dhcp_discovery_falls_back_to_manual(
    hass: HomeAssistant, discovery_data
) -> None:
    """Test we can process the discovery from dhcp but roomba discovery cannot find the specific device."""

    mocked_roomba = _create_mocked_roomba(
        roomba_connected=True,
        master_state={"state": {"reported": {"name": "myroomba"}}},
    )

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_DHCP},
            data=discovery_data,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
    )
    await hass.async_block_till_done()
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] is None
    assert result2["step_id"] == "manual"

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: MOCK_IP},
        )
    await hass.async_block_till_done()
    assert result3["type"] is FlowResultType.FORM
    assert result3["errors"] is None

    with (
        patch(
            "homeassistant.components.roomba.config_flow.RoombaFactory.create_roomba",
            return_value=mocked_roomba,
        ),
        patch(
            "homeassistant.components.roomba.config_flow.RoombaPassword",
            _mocked_getpassword,
        ),
        patch(
            "homeassistant.components.roomba.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result3["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert result4["title"] == "robot_name"
    assert result4["result"].unique_id == "BLID"
    assert result4["data"] == {
        CONF_BLID: "BLID",
        CONF_CONTINUOUS: True,
        CONF_DELAY: DEFAULT_DELAY,
        CONF_HOST: MOCK_IP,
        CONF_PASSWORD: "password",
    }
    assert len(mock_setup_entry.mock_calls) == 1