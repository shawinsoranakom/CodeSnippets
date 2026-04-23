async def test_user_setup_replaces_ignored_device(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FAKE_ADDRESS_1,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch_async_discovered_service_info([FAKE_SERVICE_INFO_1]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pick_device"

    # Verify the ignored device is in the dropdown
    assert FAKE_ADDRESS_1 in result["data_schema"].schema[CONF_ADDRESS].container

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_ADDRESS: FAKE_ADDRESS_1}
    )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == FAKE_ADDRESS_1
    assert result2["data"] == {CONF_ADDRESS: FAKE_ADDRESS_1}
    assert result2["result"].unique_id == FAKE_ADDRESS_1

    mock_setup_entry.assert_called_once()