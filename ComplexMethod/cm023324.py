async def test_happy_path(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    open_api: OpenAPI,
    aioambient: AsyncMock,
    devices_by_location: list[dict[str, Any]],
    config_entry: ConfigEntry,
) -> None:
    """Test the happy path."""

    setup_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert setup_result["type"] is FlowResultType.FORM
    assert setup_result["step_id"] == "user"

    with patch.object(
        open_api,
        "get_devices_by_location",
        AsyncMock(return_value=devices_by_location),
    ):
        user_result = await hass.config_entries.flow.async_configure(
            setup_result["flow_id"],
            {"location": {"latitude": 10.0, "longitude": 20.0, "radius": 1.0}},
        )

    assert user_result["type"] is FlowResultType.FORM
    assert user_result["step_id"] == "station"

    stations_result = await hass.config_entries.flow.async_configure(
        user_result["flow_id"],
        {
            "station": "AA:AA:AA:AA:AA:AA",
        },
    )

    assert stations_result["type"] is FlowResultType.CREATE_ENTRY
    assert stations_result["title"] == config_entry.title
    assert stations_result["data"] == config_entry.data
    assert len(mock_setup_entry.mock_calls) == 1