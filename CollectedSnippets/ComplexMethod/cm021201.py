async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=SENSIRION_SERVICE_INFO.address,
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.sensirion_ble.config_flow.async_discovered_service_info",
        return_value=[SENSIRION_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert (
        SENSIRION_SERVICE_INFO.address
        in result["data_schema"].schema["address"].container
    )

    with patch(
        "homeassistant.components.sensirion_ble.async_setup_entry", return_value=True
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": SENSIRION_SERVICE_INFO.address},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == CONFIGURED_NAME
    assert result2["data"] == {}
    assert result2["result"].unique_id == SENSIRION_SERVICE_INFO.address