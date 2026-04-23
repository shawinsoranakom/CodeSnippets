async def test_hassio_discovery_flow(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker, otbr_addon_info
) -> None:
    """Test the hassio discovery flow."""
    url = "http://core-silabs-multiprotocol:8081"
    aioclient_mock.get(f"{url}/node/dataset/active", text="aa")

    with patch(
        "homeassistant.components.otbr.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_init(
            otbr.DOMAIN, context={"source": "hassio"}, data=HASSIO_DATA
        )

    expected_data = {
        "url": f"http://{HASSIO_DATA.config['host']}:{HASSIO_DATA.config['port']}",
    }

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Silicon Labs Multiprotocol"
    assert result["data"] == expected_data
    assert result["options"] == {}
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(otbr.DOMAIN)[0]
    assert config_entry.data == expected_data
    assert config_entry.options == {}
    assert config_entry.title == "Silicon Labs Multiprotocol"
    assert config_entry.unique_id == HASSIO_DATA.uuid