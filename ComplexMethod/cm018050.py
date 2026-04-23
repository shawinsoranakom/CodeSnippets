async def test_serviceregistry_service_that_not_exists(hass: HomeAssistant) -> None:
    """Test remove service that not exists."""
    calls_remove = async_capture_events(hass, EVENT_SERVICE_REMOVED)
    assert not hass.services.has_service("test_xxx", "test_yyy")
    hass.services.async_remove("test_xxx", "test_yyy")
    await hass.async_block_till_done()
    assert len(calls_remove) == 0

    with pytest.raises(ServiceNotFound) as exc:
        await hass.services.async_call("test_do_not", "exist", {})
    assert exc.value.translation_domain == "homeassistant"
    assert exc.value.translation_key == "service_not_found"
    assert exc.value.translation_placeholders == {
        "domain": "test_do_not",
        "service": "exist",
    }
    assert exc.value.domain == "test_do_not"
    assert exc.value.service == "exist"

    assert str(exc.value) == "Action test_do_not.exist not found"