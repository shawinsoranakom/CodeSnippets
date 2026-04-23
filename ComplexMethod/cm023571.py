async def test_form(hass: HomeAssistant, get_camera: CameraInfoModel) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with (
        patch(
            "homeassistant.components.trafikverket_camera.config_flow.TrafikverketCamera.async_get_cameras",
            return_value=[get_camera],
        ),
        patch(
            "homeassistant.components.trafikverket_camera.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_API_KEY: "1234567890",
                CONF_LOCATION: "Test loc",
            },
        )
        await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Test Camera"
    assert result2["data"] == {
        "api_key": "1234567890",
        "id": "1234",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert result2["result"].unique_id == "trafikverket_camera-1234"