async def test_form(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_device, config
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "pyecoforest.api.EcoforestApi.get",
        return_value=mock_device,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            config,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert "result" in result
    assert result["result"].unique_id == "1234"
    assert result["title"] == "Ecoforest 1234"
    assert result["data"] == {
        CONF_HOST: "1.1.1.1",
        CONF_USERNAME: "test-username",
        CONF_PASSWORD: "test-password",
    }
    assert len(mock_setup_entry.mock_calls) == 1