async def test_bluetooth_discovery_errors(
    hass: HomeAssistant,
    mock_lamarzocco: MagicMock,
    mock_cloud_client: MagicMock,
) -> None:
    """Test bluetooth discovery errors."""
    service_info = get_bluetooth_service_info(
        ModelName.GS3_MP, mock_lamarzocco.serial_number
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=service_info,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    original_return = deepcopy(mock_cloud_client.list_things.return_value)
    mock_cloud_client.list_things.return_value[0].serial_number = "GS98765"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "machine_not_found"}
    assert len(mock_cloud_client.list_things.mock_calls) == 1

    mock_cloud_client.list_things.return_value = original_return
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert result["title"] == "GS012345"
    assert result["data"] == {
        **USER_INPUT,
        CONF_MAC: "aa:bb:cc:dd:ee:ff",
        CONF_TOKEN: None,
        CONF_INSTALLATION_KEY: MOCK_INSTALLATION_KEY,
    }