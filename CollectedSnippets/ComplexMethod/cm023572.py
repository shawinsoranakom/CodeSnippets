async def test_form_multiple_cameras(
    hass: HomeAssistant,
    get_cameras: list[CameraInfoModel],
    get_camera2: CameraInfoModel,
) -> None:
    """Test we get the form with multiple cameras."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
        return_value=get_cameras,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[get_camera2],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ID: "5678",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Camera2"
    assert result["data"] == {
        "api_key": "1234567890",
        "id": "5678",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert result["result"].unique_id == "trafikverket_camera-5678"