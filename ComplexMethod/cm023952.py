async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user flow can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="AA:BB:CC:DD:EE:FF",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.kulersky.config_flow.async_discovered_service_info",
        return_value=[KULERSKY_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": SOURCE_USER},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert "AA:BB:CC:DD:EE:FF" in result["data_schema"].schema[CONF_ADDRESS].container

    with patch("pykulersky.Light", Mock(return_value=AsyncMock())):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ADDRESS: "AA:BB:CC:DD:EE:FF"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "KulerLight (EEFF)"
    assert result2["data"] == {
        CONF_ADDRESS: "AA:BB:CC:DD:EE:FF",
    }
    assert result2["result"].unique_id == "AA:BB:CC:DD:EE:FF"