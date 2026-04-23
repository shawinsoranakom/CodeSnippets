async def test_pair_form_errors_on_start(
    hass: HomeAssistant, controller, exception, expected
) -> None:
    """Test various pairing errors."""

    device = setup_mock_accessory(controller)
    discovery_info = get_device_discovery_info(device)

    # Device is discovered
    result = await hass.config_entries.flow.async_init(
        "homekit_controller",
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=discovery_info,
    )

    assert get_flow_context(hass, result) == {
        "title_placeholders": {"name": "TestDevice", "category": "Outlet"},
        "unique_id": "00:00:00:00:00:00",
        "source": config_entries.SOURCE_ZEROCONF,
    }

    # User initiates pairing - device refuses to enter pairing mode
    test_exc = exception("error")
    with patch.object(device, "async_start_pairing", side_effect=test_exc):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={"pairing_code": "111-22-333"}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["pairing_code"] == expected

    assert get_flow_context(hass, result) == {
        "dismiss_protected": True,
        "title_placeholders": {"name": "TestDevice", "category": "Outlet"},
        "unique_id": "00:00:00:00:00:00",
        "source": config_entries.SOURCE_ZEROCONF,
    }

    # User gets back the form
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    # User re-tries entering pairing code
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"pairing_code": "111-22-333"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Koogeek-LS1-20833F"