async def test_zeroconf_flow_create_entry(
    hass: HomeAssistant, device1_requests_mock_standby: Mocker
) -> None:
    """Test the zeroconf flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address(DEVICE_1_IP),
            ip_addresses=[ip_address(DEVICE_1_IP)],
            port=8090,
            hostname="Bose-SM2-060000000001.local.",
            type="_soundtouch._tcp.local.",
            name=f"{DEVICE_1_NAME}._soundtouch._tcp.local.",
            properties={
                "DESCRIPTION": "SoundTouch",
                "MAC": DEVICE_1_ID,
                "MANUFACTURER": "Bose Corporation",
                "MODEL": "SoundTouch",
            },
        ),
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "zeroconf_confirm"
    assert result.get("description_placeholders") == {"name": DEVICE_1_NAME}

    with patch(
        "homeassistant.components.soundtouch.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert len(mock_setup_entry.mock_calls) == 1

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == DEVICE_1_NAME
    assert result.get("data") == {
        CONF_HOST: DEVICE_1_IP,
    }
    assert "result" in result
    assert result["result"].unique_id == DEVICE_1_ID
    assert result["result"].title == DEVICE_1_NAME