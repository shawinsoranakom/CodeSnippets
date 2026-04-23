async def test_setups(hass: HomeAssistant, protocol, connection, title) -> None:
    """Test flow for setting up the available AlarmDecoder protocols."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PROTOCOL: protocol},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "protocol"

    with (
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.open"),
        patch("homeassistant.components.alarmdecoder.config_flow.AdExt.close"),
        patch(
            "homeassistant.components.alarmdecoder.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], connection
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == title
        assert result["data"] == {
            **connection,
            CONF_PROTOCOL: protocol,
        }
        await hass.async_block_till_done()

    assert len(mock_setup_entry.mock_calls) == 1