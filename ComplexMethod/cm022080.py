async def test_user_setup_replaces_ignored_device(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_discovered_service_info: AsyncMock,
) -> None:
    """Test the user flow can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="aa:bb:cc:dd:ee:ff",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert "aa:bb:cc:dd:ee:ff" in result["data_schema"].schema[CONF_ADDRESS].container

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_ADDRESS: "aa:bb:cc:dd:ee:ff"},
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["result"].unique_id == "aa:bb:cc:dd:ee:ff"
    assert result2["title"] == "FM210 aa:bb:cc:dd:ee:ff"
    assert result2["data"] == {CONF_ADDRESS: "aa:bb:cc:dd:ee:ff", CONF_MODEL: "FM210"}