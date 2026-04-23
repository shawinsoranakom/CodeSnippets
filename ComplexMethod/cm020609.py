async def test_flow_user_init_data_error_and_recover(
    hass: HomeAssistant, raise_error, text_error
) -> None:
    """Test exceptions and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.lupusec.config_flow.lupupy.Lupusec",
        side_effect=raise_error,
    ) as mock_initialize_lupusec:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DATA_STEP,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": text_error}

    assert len(mock_initialize_lupusec.mock_calls) == 1

    # Recover
    with (
        patch(
            "homeassistant.components.lupusec.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
        patch(
            "homeassistant.components.lupusec.config_flow.lupupy.Lupusec",
        ) as mock_initialize_lupusec,
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_DATA_STEP,
        )

    await hass.async_block_till_done()

    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == MOCK_DATA_STEP[CONF_HOST]
    assert result3["data"] == MOCK_DATA_STEP
    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_initialize_lupusec.mock_calls) == 1