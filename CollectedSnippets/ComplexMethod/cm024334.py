async def test_form_with_discovery(hass: HomeAssistant) -> None:
    """Test we can also discovery the device during manual setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        _patch_discovery(),
        patch(
            "homeassistant.components.steamist.config_flow.Steamist.async_get_status"
        ),
        patch(
            "homeassistant.components.steamist.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "host": "127.0.0.1",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == DEVICE_NAME
    assert result2["data"] == DEFAULT_ENTRY_DATA
    assert result2["context"]["unique_id"] == FORMATTED_MAC_ADDRESS
    assert len(mock_setup_entry.mock_calls) == 1