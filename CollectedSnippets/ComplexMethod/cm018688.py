async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.keymitt_ble.config_flow.async_discovered_service_info",
        return_value=[SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    # Verify the ignored device is in the dropdown
    assert "aa:bb:cc:dd:ee:ff" in result["data_schema"].schema["address"].container

    with patch_microbot_api():
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "link"

    with patch_microbot_api(), patch_async_setup_entry() as mock_setup_entry:
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["result"].data == {
        CONF_ADDRESS: "aa:bb:cc:dd:ee:ff",
        CONF_ACCESS_TOKEN: ANY,
    }
    assert result3["result"].unique_id == "aa:bb:cc:dd:ee:ff"
    assert len(mock_setup_entry.mock_calls) == 1