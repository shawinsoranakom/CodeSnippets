async def test_zeroconf_discovery(hass: HomeAssistant) -> None:
    """Test zeroconf discovery setup flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=ZEROCONF_DATA
    )

    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    with patch(
        "homeassistant.components.rabbitair.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: TEST_NAME + ".local",
                CONF_ACCESS_TOKEN: TEST_TOKEN,
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == TEST_TITLE
    assert result2["data"] == {
        CONF_HOST: TEST_NAME + ".local",
        CONF_ACCESS_TOKEN: TEST_TOKEN,
        CONF_MAC: TEST_MAC,
    }
    assert result2["result"].unique_id == TEST_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=ZEROCONF_DATA
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"