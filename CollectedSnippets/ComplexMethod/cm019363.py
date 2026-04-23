async def test_form_user(hass: HomeAssistant) -> None:
    """Test we can setup by the user."""
    await setup.async_setup_component(hass, DOMAIN, {})
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    with (
        patch(
            "homeassistant.components.mullvad.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.mullvad.config_flow.MullvadAPI"
        ) as mock_mullvad_api,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Mullvad VPN"
    assert result2["data"] == {}
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_mullvad_api.mock_calls) == 1