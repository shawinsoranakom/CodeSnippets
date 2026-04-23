async def test_dhcp_discovery_and_roomba_discovery_finds(
    hass: HomeAssistant,
    discovery_data: tuple[str, DhcpServiceInfo | ZeroconfServiceInfo],
) -> None:
    """Test we can process the discovery from dhcp and roomba discovery matches the device."""

    mocked_roomba = _create_mocked_roomba(
        roomba_connected=True,
        master_state={"state": {"reported": {"name": "myroomba"}}},
    )
    source, discovery = discovery_data

    with patch(
        "homeassistant.components.roomba.config_flow.RoombaDiscovery", _mocked_discovery
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=discovery,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "link"
    assert result["description_placeholders"] == {"name": "robot_name"}

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
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "robot_name"
    assert result2["result"].unique_id == "BLID"
    assert result2["data"] == {
        CONF_BLID: "BLID",
        CONF_CONTINUOUS: True,
        CONF_DELAY: DEFAULT_DELAY,
        CONF_HOST: MOCK_IP,
        CONF_PASSWORD: "password",
    }
    assert len(mock_setup_entry.mock_calls) == 1