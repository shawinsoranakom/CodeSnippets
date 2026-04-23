async def test_zeroconf_flow(
    hass: HomeAssistant,
    mock_smlight_client: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the zeroconf flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=DISCOVERY_INFO
    )

    assert result["description_placeholders"] == {"host": MOCK_DEVICE_NAME}
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm_discovery"

    progress = hass.config_entries.flow.async_progress()
    assert len(progress) == 1
    assert progress[0]["flow_id"] == result["flow_id"]
    assert progress[0]["context"]["confirm_only"] is True

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["context"]["source"] == "zeroconf"
    assert result2["context"]["unique_id"] == "aa:bb:cc:dd:ee:ff"
    assert result2["title"] == "slzb-06"
    assert result2["data"] == {
        CONF_HOST: MOCK_HOST,
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_smlight_client.get_info.mock_calls) == 2