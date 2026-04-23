async def test_passing_variables(hass: HomeAssistant) -> None:
    """Test different ways of passing in variables."""
    mock_restore_cache(hass, ())
    calls = []
    context = Context()

    @callback
    def record_call(service):
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "sequence": {
                        "action": "test.script",
                        "data_template": {"hello": "{{ greeting }}"},
                    }
                }
            }
        },
    )

    await hass.services.async_call(
        DOMAIN, "test", {"greeting": "world"}, context=context
    )

    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].context is context
    assert calls[0].data["hello"] == "world"

    await hass.services.async_call(
        "script", "test", {"greeting": "universe"}, context=context
    )

    await hass.async_block_till_done()

    assert len(calls) == 2
    assert calls[1].context is context
    assert calls[1].data["hello"] == "universe"