async def test_user_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_NAME: "Name",
            CONF_LATITUDE: 52.42,
            CONF_LONGITUDE: 4.42,
            CONF_AZIMUTH: 142,
            CONF_DECLINATION: 42,
            CONF_MODULES_POWER: 4242,
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "Name"
    assert config_entry.unique_id is None
    assert config_entry.data == {
        CONF_LATITUDE: 52.42,
        CONF_LONGITUDE: 4.42,
    }
    assert config_entry.options == {}

    # Verify a plane subentry was created
    plane_subentries = config_entry.get_subentries_of_type(SUBENTRY_TYPE_PLANE)
    assert len(plane_subentries) == 1
    subentry = plane_subentries[0]
    assert subentry.subentry_type == SUBENTRY_TYPE_PLANE
    assert subentry.data == {
        CONF_DECLINATION: 42,
        CONF_AZIMUTH: 142,
        CONF_MODULES_POWER: 4242,
    }
    assert subentry.title == "42° / 142° / 4242W"

    assert len(mock_setup_entry.mock_calls) == 1