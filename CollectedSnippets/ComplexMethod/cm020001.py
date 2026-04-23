async def test_flow_hassio_discovery(hass: HomeAssistant) -> None:
    """Test hassio discovery flow works."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=HassioServiceInfo(
            config={
                "addon": "Mock Addon",
                CONF_HOST: "mock-deconz",
                CONF_PORT: 80,
                CONF_SERIAL: BRIDGE_ID,
                CONF_API_KEY: API_KEY,
            },
            name="Mock Addon",
            slug="deconz",
            uuid="1234",
        ),
        context={"source": SOURCE_HASSIO},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "hassio_confirm"
    assert result["description_placeholders"] == {"addon": "Mock Addon"}

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert (
        flows[0].get("context", {}).get("configuration_url") == HASSIO_CONFIGURATION_URL
    )

    with patch(
        "homeassistant.components.deconz.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].data == {
        CONF_HOST: "mock-deconz",
        CONF_PORT: 80,
        CONF_API_KEY: API_KEY,
    }
    assert len(mock_setup_entry.mock_calls) == 1