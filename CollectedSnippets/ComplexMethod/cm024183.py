async def test_mqtt_discovery_flow_starts_once(
    hass: HomeAssistant,
    mqtt_client_mock: MqttMockPahoClient,
    caplog: pytest.LogCaptureFixture,
    mock_mqtt_flow: config_entries.ConfigFlow,
    mqtt_data_flow_calls: list[MqttServiceInfo],
) -> None:
    """Check MQTT integration discovery starts a flow once.

    A flow should be started once after discovery,
    and after an entry was removed, to trigger re-discovery.
    """
    mock_integration(
        hass, MockModule(domain="comp", async_setup_entry=AsyncMock(return_value=True))
    )
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
        mock_config_flow("comp", mock_mqtt_flow),
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await mqtt.async_subscribe(hass, "homeassistant/status", wait_birth)
        hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
        await birth.wait()

        assert ("comp/discovery/#", 0) in help_all_subscribe_calls(mqtt_client_mock)

        # Test the initial flow
        async_fire_mqtt_message(hass, "comp/discovery/bla/config1", "initial message")
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(mqtt_data_flow_calls) == 1
        assert mqtt_data_flow_calls[0].topic == "comp/discovery/bla/config1"
        assert mqtt_data_flow_calls[0].payload == "initial message"

        # Test we can ignore updates if they are the same
        with caplog.at_level(logging.DEBUG):
            async_fire_mqtt_message(
                hass, "comp/discovery/bla/config1", "initial message"
            )
            await hass.async_block_till_done(wait_background_tasks=True)
            assert "Ignoring already processed discovery message" in caplog.text
            assert len(mqtt_data_flow_calls) == 1

        # Test we can apply updates
        async_fire_mqtt_message(hass, "comp/discovery/bla/config1", "update message")
        await hass.async_block_till_done(wait_background_tasks=True)

        assert len(mqtt_data_flow_calls) == 2
        assert mqtt_data_flow_calls[1].topic == "comp/discovery/bla/config1"
        assert mqtt_data_flow_calls[1].payload == "update message"

        # Test we set up multiple entries
        async_fire_mqtt_message(hass, "comp/discovery/bla/config2", "initial message")
        await hass.async_block_till_done(wait_background_tasks=True)

        assert len(mqtt_data_flow_calls) == 3
        assert mqtt_data_flow_calls[2].topic == "comp/discovery/bla/config2"
        assert mqtt_data_flow_calls[2].payload == "initial message"

        # Test we update multiple entries
        async_fire_mqtt_message(hass, "comp/discovery/bla/config2", "update message")
        await hass.async_block_till_done(wait_background_tasks=True)

        assert len(mqtt_data_flow_calls) == 4
        assert mqtt_data_flow_calls[3].topic == "comp/discovery/bla/config2"
        assert mqtt_data_flow_calls[3].payload == "update message"

        # Test an empty message triggers a flow to allow cleanup (if needed)
        async_fire_mqtt_message(hass, "comp/discovery/bla/config2", "")
        await hass.async_block_till_done(wait_background_tasks=True)

        assert len(mqtt_data_flow_calls) == 5
        assert mqtt_data_flow_calls[4].topic == "comp/discovery/bla/config2"
        assert mqtt_data_flow_calls[4].payload == ""

        # Cleanup the the second entry
        assert (
            entry := hass.config_entries.async_entry_for_domain_unique_id(
                "comp", "comp/discovery/bla/config2"
            )
        ) is not None
        await hass.config_entries.async_remove(entry.entry_id)
        assert len(hass.config_entries.async_entries(domain="comp")) == 1

        # Remove remaining entry1 and assert this triggers an
        # automatic re-discovery flow with latest config
        assert (
            entry := hass.config_entries.async_entry_for_domain_unique_id(
                "comp", "comp/discovery/bla/config1"
            )
        ) is not None
        assert entry.unique_id == "comp/discovery/bla/config1"
        await hass.config_entries.async_remove(entry.entry_id)
        assert len(hass.config_entries.async_entries(domain="comp")) == 0

        # Wait for re-discovery flow to complete
        await hass.async_block_till_done(wait_background_tasks=True)
        assert len(mqtt_data_flow_calls) == 6
        assert mqtt_data_flow_calls[5].topic == "comp/discovery/bla/config1"
        assert mqtt_data_flow_calls[5].payload == "update message"

        # Re-discovery triggered the config flow
        assert len(hass.config_entries.async_entries(domain="comp")) == 1

        assert not mqtt_client_mock.unsubscribe.called