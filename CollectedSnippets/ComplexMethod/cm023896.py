async def test_user_setup(hass: HomeAssistant, mock_device, mock_setup_entry) -> None:
    """Test manually setting up."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    assert "flow_id" in result

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
        },
    )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == f"{MOCKED_DEVICE_TYPE}_{MOCKED_DEVICE_SERIAL_NUMBER}"
    assert result.get("data") == {
        CONF_HOST: MOCKED_DEVICE_IP_ADDRESS,
        ATTR_SERIAL_NUMBER: MOCKED_DEVICE_SERIAL_NUMBER,
        CONF_TYPE: MOCKED_DEVICE_TYPE,
        ATTR_HW_VERSION: MOCKED_DEVICE_BOARD_REV,
    }
    assert "result" in result
    assert len(mock_setup_entry.mock_calls) == 1
    assert result.get("result").unique_id == MOCKED_DEVICE_SERIAL_NUMBER