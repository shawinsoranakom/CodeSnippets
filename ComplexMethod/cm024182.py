async def test_mqtt_integration_discovery_flow_fitering_on_redundant_payload(
    hass: HomeAssistant, mqtt_client_mock: MqttMockPahoClient, reason: str
) -> None:
    """Check MQTT integration discovery starts a flow once."""
    flow_calls: list[MqttServiceInfo] = []

    class TestFlow(config_entries.ConfigFlow):
        """Test flow."""

        async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
            """Test mqtt step."""
            flow_calls.append(discovery_info)
            return self.async_abort(reason=reason)

    mock_platform(hass, "comp.config_flow", None)

    birth = asyncio.Event()

    @callback
    def wait_birth(msg: ReceiveMessage) -> None:
        """Handle birth message."""
        birth.set()

    entry = MockConfigEntry(
        domain=mqtt.DOMAIN,
        data={mqtt.CONF_BROKER: "mock-broker"},
        options=ENTRY_DEFAULT_BIRTH_MESSAGE,
        version=mqtt.CONFIG_ENTRY_VERSION,
        minor_version=mqtt.CONFIG_ENTRY_MINOR_VERSION,
    )
    entry.add_to_hass(hass)
    with (
        patch(
            "homeassistant.components.mqtt.discovery.async_get_mqtt",
            return_value={"comp": ["comp/discovery/#"]},
        ),
        mock_config_flow("comp", TestFlow),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await mqtt.async_subscribe(hass, "homeassistant/status", wait_birth)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await birth.wait()

        assert ("comp/discovery/#", 0) in help_all_subscribe_calls(mqtt_client_mock)
        assert not mqtt_client_mock.unsubscribe.called
        mqtt_client_mock.reset_mock()
        assert len(flow_calls) == 0

        await hass.async_block_till_done(wait_background_tasks=True)
        async_fire_mqtt_message(hass, "comp/discovery/bla/config", "initial message")
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(flow_calls) == 1

        # A redundant message gets does not start a new flow
        await hass.async_block_till_done(wait_background_tasks=True)
        async_fire_mqtt_message(hass, "comp/discovery/bla/config", "initial message")
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(flow_calls) == 1

        # An updated message gets starts a new flow
        await hass.async_block_till_done(wait_background_tasks=True)
        async_fire_mqtt_message(hass, "comp/discovery/bla/config", "update message")
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(flow_calls) == 2