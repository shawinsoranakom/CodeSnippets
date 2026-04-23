async def test_create_entry_gps(
    hass: HomeAssistant, entity_registry: er.EntityRegistry, mock_dwdwfsapi: MagicMock
) -> None:
    """Test that the full config flow works for a device tracker."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM

    # Test for missing registry entry error.
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "entity_not_found"}

    # Test for missing device tracker error.
    registry_entry = entity_registry.async_get_or_create(
        "device_tracker", DOMAIN, "uuid", suggested_object_id="test_gps"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "entity_not_found"}

    # Test for missing attribute error.
    hass.states.async_set(
        DEMO_CONFIG_ENTRY_GPS[CONF_REGION_DEVICE_TRACKER],
        STATE_HOME,
        {ATTR_LONGITUDE: "7.610263"},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "attribute_not_found"}

    # Test for invalid provided identifier.
    hass.states.async_set(
        DEMO_CONFIG_ENTRY_GPS[CONF_REGION_DEVICE_TRACKER],
        STATE_HOME,
        {ATTR_LATITUDE: "50.180454", ATTR_LONGITUDE: "7.610263"},
    )

    mock_dwdwfsapi.__bool__.return_value = False
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_identifier"}

    # Test for successfully created entry.
    mock_dwdwfsapi.__bool__.return_value = True
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=DEMO_CONFIG_ENTRY_GPS
    )

    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test_gps"
    assert result["data"] == {
        CONF_REGION_DEVICE_TRACKER: registry_entry.id,
    }