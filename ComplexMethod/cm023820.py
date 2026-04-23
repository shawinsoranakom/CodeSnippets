async def test_user_form_with_non_bridge(hass: HomeAssistant) -> None:
    """Test setup a smart by bond fan."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch_bond_version(return_value={"bondid": "KXXX12345"}),
        patch_bond_device_ids(return_value=["f6776c11"]),
        patch_bond_device_properties(),
        patch_bond_device(
            return_value={
                "name": "New Fan",
            }
        ),
        patch_bond_bridge(return_value={}),
        patch_bond_device_state(),
        _patch_async_setup_entry() as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "some host", CONF_ACCESS_TOKEN: "test-token"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "New Fan"
    assert result2["data"] == {
        CONF_HOST: "some host",
        CONF_ACCESS_TOKEN: "test-token",
    }
    assert result2["result"].unique_id == "KXXX12345"
    assert len(mock_setup_entry.mock_calls) == 1