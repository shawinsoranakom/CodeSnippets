async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.ld2410_ble.config_flow.async_discovered_service_info",
        return_value=[LD2410_BLE_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert "AA:BB:CC:DD:EE:FF" in result["data_schema"].schema["address"].container

    with (
        patch(
            "homeassistant.components.ld2410_ble.config_flow.LD2410BLE.initialise",
        ),
        patch(
            "homeassistant.components.ld2410_ble.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: LD2410_BLE_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == LD2410_BLE_DISCOVERY_INFO.name
    assert result2["data"] == {
        CONF_ADDRESS: LD2410_BLE_DISCOVERY_INFO.address,
    }
    assert result2["result"].unique_id == LD2410_BLE_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1