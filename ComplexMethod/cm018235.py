async def test_config_flow(
    hass: HomeAssistant,
    entity_type: str,
    extra_input: dict[str, Any],
    extra_options: dict[str, Any],
) -> None:
    """Test the config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.MENU

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": entity_type},
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == entity_type

    with patch(
        "homeassistant.components.random.async_setup_entry", wraps=async_setup_entry
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My random entity",
                **extra_input,
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My random entity"
    assert result["data"] == {}
    assert result["options"] == {
        "name": "My random entity",
        "entity_type": entity_type,
        **extra_options,
    }
    assert len(mock_setup_entry.mock_calls) == 1