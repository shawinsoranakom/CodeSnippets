async def test_async_step_integration_discovery_during_onboarding_two_adapters(
    hass: HomeAssistant,
) -> None:
    """Test setting up from integration discovery during onboarding."""
    details1 = AdapterDetails(
        address="00:00:00:00:00:01",
        sw_version="1.23.5",
        hw_version="1.2.3",
        manufacturer="ACME",
    )
    details2 = AdapterDetails(
        address="00:00:00:00:00:02",
        sw_version="1.23.5",
        hw_version="1.2.3",
        manufacturer="ACME",
    )

    with (
        patch("homeassistant.components.bluetooth.async_setup", return_value=True),
        patch(
            "homeassistant.components.bluetooth.async_setup_entry", return_value=True
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.onboarding.async_is_onboarded",
            return_value=False,
        ) as mock_onboarding,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={CONF_ADAPTER: "hci0", CONF_DETAILS: details1},
        )
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
            data={CONF_ADAPTER: "hci1", CONF_DETAILS: details2},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "ACME Unknown (00:00:00:00:00:01)"
    assert result["data"] == {}

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "ACME Unknown (00:00:00:00:00:02)"
    assert result2["data"] == {}

    assert len(mock_setup_entry.mock_calls) == 2
    assert len(mock_onboarding.mock_calls) == 2