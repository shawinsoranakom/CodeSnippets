async def test_discover_flow_multiple_devices_found(
    hass: HomeAssistant,
    mock_airos_client: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_discovery_method: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test discovery flow with multiple devices found, requiring a selection step."""
    mock_discovery_method.return_value = {
        MOCK_DISC_DEV1[MAC_ADDRESS]: MOCK_DISC_DEV1,
        MOCK_DISC_DEV2[MAC_ADDRESS]: MOCK_DISC_DEV2,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert "discovery" in result["menu_options"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "discovery"}
    )

    assert result["type"] is FlowResultType.SHOW_PROGRESS
    assert result["step_id"] == "discovery"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "select_device"

    expected_options = {
        MOCK_DISC_DEV1[MAC_ADDRESS]: (
            f"{MOCK_DISC_DEV1[HOSTNAME]} ({MOCK_DISC_DEV1[IP_ADDRESS]})"
        ),
        MOCK_DISC_DEV2[MAC_ADDRESS]: (
            f"{MOCK_DISC_DEV2[HOSTNAME]} ({MOCK_DISC_DEV2[IP_ADDRESS]})"
        ),
    }
    actual_options = result["data_schema"].schema[vol.Required(MAC_ADDRESS)].container
    assert actual_options == expected_options

    # Select one of the devices
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {MAC_ADDRESS: MOCK_DISC_DEV1[MAC_ADDRESS]}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "configure_device"
    assert result["description_placeholders"]["device_name"] == MOCK_DISC_DEV1[HOSTNAME]

    valid_data = DetectDeviceData(
        fw_major=8,
        mac=MOCK_DISC_DEV1[MAC_ADDRESS],
        hostname=MOCK_DISC_DEV1[HOSTNAME],
    )

    with patch(
        "homeassistant.components.airos.config_flow.async_get_firmware_data",
        new=AsyncMock(return_value=valid_data),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: DEFAULT_USERNAME,
                CONF_PASSWORD: "test-password",
                SECTION_ADVANCED_SETTINGS: MOCK_ADVANCED_SETTINGS,
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == MOCK_DISC_DEV1[HOSTNAME]
    assert result["data"][CONF_HOST] == MOCK_DISC_DEV1[IP_ADDRESS]