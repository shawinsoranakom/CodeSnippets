async def test_form_auth(hass: HomeAssistant) -> None:
    """Test we handle auth."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"host": "1.1.1.1"},
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "auth"

    with patch(
        "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
        return_value=False,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "mock-user",
                "password": "mock-pass",
            },
        )
        await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "auth"
    assert result3["errors"] == {"base": "invalid_auth"}

    with (
        patch(
            "homeassistant.components.iotawatt.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.iotawatt.config_flow.Iotawatt.connect",
            return_value=True,
        ),
    ):
        result4 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "mock-user",
                "password": "mock-pass",
            },
        )
        await hass.async_block_till_done()

    assert result4["type"] is FlowResultType.CREATE_ENTRY
    assert len(mock_setup_entry.mock_calls) == 1
    assert result4["data"] == {
        "host": "1.1.1.1",
        "username": "mock-user",
        "password": "mock-pass",
    }