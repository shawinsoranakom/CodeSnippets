async def test_state_changed(hass: HomeAssistant) -> None:
    """Test event listener."""
    with (
        patch("homeassistant.components.datadog.DogStatsd") as mock_statsd_class,
        patch(
            "homeassistant.components.datadog.config_flow.DogStatsd", mock_statsd_class
        ),
    ):
        mock_statsd = mock_statsd_class.return_value
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={
                "host": "host",
                "port": DEFAULT_PORT,
            },
            options={"prefix": "ha", "rate": DEFAULT_RATE},
        )
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)

        valid = {"1": 1, "1.0": 1.0, STATE_ON: 1, STATE_OFF: 0}

        attributes = {"elevation": 3.2, "temperature": 5.0, "up": True, "down": False}

        for in_, out in valid.items():
            state = create_mock_state("sensor.foobar", in_, attributes)
            hass.states.async_set(state.entity_id, state.state, state.attributes)
            await hass.async_block_till_done()
            assert mock_statsd.gauge.call_count == 5

            for attribute, value in attributes.items():
                value = int(value) if isinstance(value, bool) else value
                mock_statsd.gauge.assert_has_calls(
                    [
                        mock.call(
                            f"ha.sensor.{attribute}",
                            value,
                            sample_rate=1,
                            tags=[f"entity:{state.entity_id}"],
                        )
                    ]
                )

            assert mock_statsd.gauge.call_args == mock.call(
                "ha.sensor",
                out,
                sample_rate=1,
                tags=[f"entity:{state.entity_id}"],
            )

            mock_statsd.gauge.reset_mock()

        for invalid in ("foo", "", object):
            hass.states.async_set("domain.test", invalid, {})
            await hass.async_block_till_done()
            assert not mock_statsd.gauge.called