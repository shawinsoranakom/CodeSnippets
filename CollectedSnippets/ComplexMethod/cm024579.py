async def test_user_flow_create_entry(
    hass: HomeAssistant, device1_requests_mock_standby: Mocker
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={CONF_SOURCE: SOURCE_USER},
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"

    with patch(
        "homeassistant.components.soundtouch.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: DEVICE_1_IP,
            },
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