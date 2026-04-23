async def test_user_step_replaces_ignored_device(
    hass: HomeAssistant, mock_desk_api: MagicMock
) -> None:
    """Test user step replaces ignored devices."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=IDASEN_DISCOVERY_INFO.address,
        source=config_entries.SOURCE_IGNORE,
        data={CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.idasen_desk.config_flow.async_discovered_service_info",
        return_value=[NOT_IDASEN_DISCOVERY_INFO, IDASEN_DISCOVERY_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.idasen_desk.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == IDASEN_DISCOVERY_INFO.name
    assert result2["data"] == {
        CONF_ADDRESS: IDASEN_DISCOVERY_INFO.address,
    }
    assert result2["result"].unique_id == IDASEN_DISCOVERY_INFO.address
    assert len(mock_setup_entry.mock_calls) == 1