async def test_sun_renders_once_per_sensor(hass: HomeAssistant) -> None:
    """Test sun change renders the template only once per sensor."""

    now = dt_util.utcnow()
    hass.states.async_set(
        "sun.sun", "above_horizon", {"elevation": 45.3, "next_rising": now}
    )
    await hass.async_block_till_done()

    assert len(hass.states.async_all()) == 3

    assert hass.states.get("sensor.solar_angle").state == "45.3"
    assert hass.states.get("sensor.sunrise").state == str(now)

    async_render_calls = []

    @callback
    def _record_async_render(self, *args, **kwargs):
        """Catch async_render."""
        async_render_calls.append(self.template)
        return 75

    later = dt_util.utcnow()

    with patch.object(Template, "async_render", _record_async_render):
        hass.states.async_set("sun.sun", {"elevation": 50, "next_rising": later})
        await hass.async_block_till_done()

    assert hass.states.get("sensor.solar_angle").state == "75"
    assert hass.states.get("sensor.sunrise").state == "75"

    assert len(async_render_calls) == 2
    assert set(async_render_calls) == {
        "{{ state_attr('sun.sun', 'elevation') }}",
        "{{ state_attr('sun.sun', 'next_rising') }}",
    }