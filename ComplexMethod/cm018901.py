async def test_configure_with_discover(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test configure with discover."""
    with patch(
        "pynobo.nobo.async_discover_hubs",
        return_value=[("1.1.1.1", "123456789")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "device": "1.1.1.1",
        },
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {}
    assert result2["step_id"] == "selected"

    with (
        patch("pynobo.nobo.async_connect_hub", return_value=True) as mock_connect,
        patch(
            "pynobo.nobo.hub_info",
            new_callable=PropertyMock,
            create=True,
            return_value={"name": "My Nobø Ecohub"},
        ),
    ):
        result3 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {
                "serial_suffix": "012",
            },
        )
        await hass.async_block_till_done()

        assert result3["type"] is FlowResultType.CREATE_ENTRY
        assert result3["title"] == "My Nobø Ecohub"
        assert result3["data"] == {
            "ip_address": "1.1.1.1",
            "serial": "123456789012",
            "auto_discovered": True,
        }
        mock_connect.assert_awaited_once_with("1.1.1.1", "123456789012")
        mock_setup_entry.assert_awaited_once()