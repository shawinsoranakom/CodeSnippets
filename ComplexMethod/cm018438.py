async def test_user_setup_replaces_ignored_device(hass: HomeAssistant) -> None:
    """Test the user initiated form can replace an ignored device."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="D0:CF:5E:5C:9B:75",
        source=SOURCE_IGNORE,
        data={},
    )
    entry.add_to_hass(hass)

    with patch(
        "homeassistant.components.kegtron.config_flow.async_discovered_service_info",
        return_value=[KEGTRON_KT100_SERVICE_INFO],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Verify the ignored device is in the dropdown
    assert "D0:CF:5E:5C:9B:75" in result["data_schema"].schema["address"].container

    with patch("homeassistant.components.kegtron.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={"address": "D0:CF:5E:5C:9B:75"},
        )
    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Kegtron KT-100 9B75"
    assert result2["data"] == {}
    assert result2["result"].unique_id == "D0:CF:5E:5C:9B:75"