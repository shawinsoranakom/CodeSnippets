async def test_form_multiple_meters_first_connected(hass: HomeAssistant) -> None:
    """Test proper flow with an EAGLE-200 with a list of meters, one of which is connected (should auto-select it)."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    # Simulate multiple meters with one connected
    class MockElectricMeter:
        def __init__(self, hardware_address, connection_status) -> None:
            self.hardware_address = hardware_address
            self.connection_status = connection_status

    meters = [
        MockElectricMeter("meter-1", "Not Joined"),
        MockElectricMeter("meter-2", "Connected"),
        MockElectricMeter("meter-3", "Not Joined"),
    ]

    with (
        patch(
            "aioeagle.EagleHub.get_device_list",
            return_value=meters,
        ),
        patch(
            "homeassistant.components.rainforest_eagle.async_setup_entry",
            return_value=True,
        ) as mock_setup_entry,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_CLOUD_ID: "abcdef",
                CONF_INSTALL_CODE: "123456",
                CONF_HOST: "192.168.1.55",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "abcdef"
    assert result["data"] == {
        CONF_TYPE: TYPE_EAGLE_200,
        CONF_HOST: "192.168.1.55",
        CONF_CLOUD_ID: "abcdef",
        CONF_INSTALL_CODE: "123456",
        CONF_HARDWARE_ADDRESS: "meter-2",
    }
    assert result["result"].unique_id == "abcdef"
    assert len(mock_setup_entry.mock_calls) == 1