async def test_user_flow_name_conflict_migrate(
    hass: HomeAssistant,
    mock_client: APIClient,
) -> None:
    """Test handle migration on name conflict."""
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DEVICE_NAME: "test"},
        unique_id="11:22:33:44:55:cc",
    )
    existing_entry.add_to_hass(hass)
    device_info = DeviceInfo(
        uses_password=False,
        name="test",
        mac_address="11:22:33:44:55:AA",
    )
    mock_client.device_info = AsyncMock(return_value=device_info)
    mock_client.list_entities_services = AsyncMock(return_value=([], []))
    mock_client.device_info_and_list_entities = AsyncMock(
        return_value=(device_info, [], [])
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data={CONF_HOST: "127.0.0.1", CONF_PORT: 6053},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "name_conflict"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "name_conflict_migrate"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "name_conflict_migrated"
    assert result["description_placeholders"] == {
        "existing_mac": "11:22:33:44:55:cc",
        "mac": "11:22:33:44:55:aa",
        "name": "test",
    }
    assert existing_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_PORT: 6053,
        CONF_PASSWORD: "",
        CONF_NOISE_PSK: "",
        CONF_DEVICE_NAME: "test",
    }
    assert existing_entry.unique_id == "11:22:33:44:55:aa"