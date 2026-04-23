async def test_pick_device_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the pick device step can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FORMATTED_MAC_ADDRESS,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with _patch_discovery(), _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.async_block_till_done()
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "pick_device"

    # Verify the ignored device is in the dropdown
    assert FORMATTED_MAC_ADDRESS in result2["data_schema"].schema[CONF_DEVICE].container

    with (
        _patch_discovery(),
        _patch_status(MOCK_ASYNC_GET_STATUS_INACTIVE),
        patch(f"{MODULE}.async_setup", return_value=True),
        patch(f"{MODULE}.async_setup_entry", return_value=True),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_DEVICE: FORMATTED_MAC_ADDRESS},
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == DEVICE_NAME
    assert result3["data"] == DEFAULT_ENTRY_DATA
    assert result3["result"].unique_id == FORMATTED_MAC_ADDRESS