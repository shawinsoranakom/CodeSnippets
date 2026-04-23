async def test_form_zeroconf_correct_oui(
    hass: HomeAssistant, doorbird_api: DoorBird
) -> None:
    """Test we can setup from zeroconf with the correct OUI source."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.5"),
            ip_addresses=[ip_address("192.168.1.5")],
            hostname="mock_hostname",
            name="Doorstation - abc123._axis-video._tcp.local.",
            port=None,
            properties={"macaddress": "1CCAE3DOORBIRD"},
            type="mock_type",
        ),
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with (
        patch("homeassistant.components.logbook.async_setup", return_value=True),
        patch(
            "homeassistant.components.doorbird.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.doorbird.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], VALID_CONFIG
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "1.2.3.4"
    assert result2["data"] == {
        "host": "1.2.3.4",
        "name": "mydoorbird",
        "password": "password",
        "username": "friend",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1