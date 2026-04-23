async def test_user_pairing_with_insecure_setup_code(
    hass: HomeAssistant, controller
) -> None:
    """Test user initiated disovers devices."""
    device = setup_mock_accessory(controller)
    device.pairing_code = "123-45-678"

    # Device is discovered
    result = await hass.config_entries.flow.async_init(
        "homekit_controller", context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert get_flow_context(hass, result) == {
        "source": config_entries.SOURCE_USER,
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"device": "TestDevice"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"

    assert get_flow_context(hass, result) == {
        "source": config_entries.SOURCE_USER,
        "unique_id": "00:00:00:00:00:00",
        "title_placeholders": {"name": "TestDevice", "category": "Other"},
    }

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"pairing_code": "123-45-678"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "pair"
    assert result["errors"] == {"pairing_code": "insecure_setup_code"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"pairing_code": "123-45-678", "allow_insecure_setup_codes": True},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Koogeek-LS1-20833F"