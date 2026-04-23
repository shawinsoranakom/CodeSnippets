async def test_discovery_link_unavailable(
    hass: HomeAssistant, source: type, type_in_discovery_info: str
) -> None:
    """Test discovery and abort if device is unavailable."""
    with (
        patch(
            "homeassistant.components.nanoleaf.config_flow.Nanoleaf.get_info",
        ),
        patch(
            "homeassistant.components.nanoleaf.config_flow.load_json_object",
            return_value={},
        ),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source},
            data=ZeroconfServiceInfo(
                ip_address=ip_address(TEST_HOST),
                ip_addresses=[ip_address(TEST_HOST)],
                hostname="mock_hostname",
                name=f"{TEST_NAME}.{type_in_discovery_info}",
                port=None,
                properties={ATTR_PROPERTIES_ID: TEST_DEVICE_ID},
                type=type_in_discovery_info,
            ),
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    context = next(
        flow["context"]
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert context["title_placeholders"] == {"name": TEST_NAME}
    assert context["unique_id"] == TEST_NAME

    with patch(
        "homeassistant.components.nanoleaf.config_flow.Nanoleaf.authorize",
        side_effect=Unavailable,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"