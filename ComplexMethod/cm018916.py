async def test_form_user_errors(
    hass: HomeAssistant,
    openwebif_device_mock: AsyncMock,
    side_effect: Exception,
    error_value: str,
) -> None:
    """Test we handle errors."""

    openwebif_device_mock.get_about.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_FULL
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == SOURCE_USER
    assert result["errors"] == {"base": error_value}

    openwebif_device_mock.get_about.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        TEST_FULL,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == TEST_FULL[CONF_HOST]
    assert result["data"] == TEST_FULL
    assert result["result"].unique_id == openwebif_device_mock.mac_address