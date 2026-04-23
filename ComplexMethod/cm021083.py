async def test_update_entity(
    hass: HomeAssistant,
    mock_dashboard: dict[str, Any],
    devices_payload: list[dict[str, Any]],
    expected_state: str,
    expected_attributes: dict[str, Any],
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test ESPHome update entity."""
    mock_dashboard["configured"] = devices_payload
    await async_get_dashboard(hass).async_refresh()

    await mock_esphome_device(
        mock_client=mock_client,
    )

    state = hass.states.get("update.test_firmware")
    assert state is not None
    assert state.state == expected_state
    for key, expected_value in expected_attributes.items():
        assert state.attributes.get(key) == expected_value

    if expected_state != "on":
        return

    # Compile failed, don't try to upload
    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.compile",
            return_value=False,
        ) as mock_compile,
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.upload",
            return_value=True,
        ) as mock_upload,
        pytest.raises(
            HomeAssistantError,
            match="compiling",
        ),
    ):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.test_firmware"},
            blocking=True,
        )

    assert len(mock_compile.mock_calls) == 1
    assert mock_compile.mock_calls[0][1][0] == "test.yaml"

    assert len(mock_upload.mock_calls) == 0

    # Compile success, upload fails
    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.compile",
            return_value=True,
        ) as mock_compile,
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.upload",
            return_value=False,
        ) as mock_upload,
        pytest.raises(
            HomeAssistantError,
            match="OTA",
        ),
    ):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.test_firmware"},
            blocking=True,
        )

    assert len(mock_compile.mock_calls) == 1
    assert mock_compile.mock_calls[0][1][0] == "test.yaml"

    assert len(mock_upload.mock_calls) == 1
    assert mock_upload.mock_calls[0][1][0] == "test.yaml"

    # Everything works
    with (
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.compile",
            return_value=True,
        ) as mock_compile,
        patch(
            "homeassistant.components.esphome.coordinator.ESPHomeDashboardAPI.upload",
            return_value=True,
        ) as mock_upload,
    ):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: "update.test_firmware"},
            blocking=True,
        )

    assert len(mock_compile.mock_calls) == 1
    assert mock_compile.mock_calls[0][1][0] == "test.yaml"

    assert len(mock_upload.mock_calls) == 1
    assert mock_upload.mock_calls[0][1][0] == "test.yaml"