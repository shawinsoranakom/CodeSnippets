async def test_full_user_flow_implementation(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full manual user flow from start to finish."""
    aioclient_mock.post(
        "http://192.168.1.123:80/mf",
        text=await async_load_fixture(hass, "device_info.json", DOMAIN),
        headers={"Content-Type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM

    with patch(
        "homeassistant.components.modern_forms.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
        )

    assert result2.get("title") == "ModernFormsFan"
    assert "data" in result2
    assert result2.get("type") is FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_HOST] == "192.168.1.123"
    assert result2["data"][CONF_MAC] == "AA:BB:CC:DD:EE:FF"
    assert len(mock_setup_entry.mock_calls) == 1