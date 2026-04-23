async def test_import(hass: HomeAssistant) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_IMPORT}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    conf = {
        "host": "127.0.0.1",
        "port": 8080,
    }

    mock_hlk_sw16_connection = await create_mock_hlk_sw16_connection(False)

    with (
        patch(
            "homeassistant.components.hlk_sw16.config_flow.connect_client",
            return_value=mock_hlk_sw16_connection,
        ),
        patch(
            "homeassistant.components.hlk_sw16.async_setup", return_value=True
        ) as mock_setup,
        patch(
            "homeassistant.components.hlk_sw16.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            conf,
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "127.0.0.1:8080"
    assert result2["data"] == {
        "host": "127.0.0.1",
        "port": 8080,
    }
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1