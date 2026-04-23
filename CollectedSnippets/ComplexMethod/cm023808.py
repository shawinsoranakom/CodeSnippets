async def test_flow_replace_ignored_device(hass: HomeAssistant) -> None:
    """Test we can replace an ignored device via discovery."""
    # Add ignored entry to simulate previously ignored device
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=FAKE_MAC,
        source=config_entries.SOURCE_IGNORE,
    )
    entry.add_to_hass(hass)
    # Patch discovery to find the same ignored device
    with _patch_discovery(), _patch_wizlight():
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pick_device"
    # Proceed with selecting the device — previously ignored
    with (
        _patch_wizlight(),
        patch(
            "homeassistant.components.wiz.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.wiz.async_setup",
            return_value=True,
        ) as mock_setup,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_DEVICE: FAKE_MAC}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "WiZ Dimmable White ABCABC"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1