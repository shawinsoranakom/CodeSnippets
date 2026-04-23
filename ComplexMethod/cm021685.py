async def assert_request_calls_service(
    namespace: str,
    name: str,
    endpoint: str,
    service: str,
    hass: HomeAssistant,
    response_type="Response",
    payload: dict[str, Any] | None = None,
    instance: str | None = None,
) -> tuple[ServiceCall, dict[str, Any]]:
    """Assert an API request calls a hass service."""
    context = Context()
    request = get_new_request(namespace, name, endpoint)
    if payload:
        request["directive"]["payload"] = payload
    if instance:
        request["directive"]["header"]["instance"] = instance

    domain, service_name = service.split(".")
    calls = async_mock_service(hass, domain, service_name)

    msg = await smart_home.async_handle_message(
        hass, get_default_config(hass), request, context
    )
    await hass.async_block_till_done()

    assert len(calls) == 1
    call = calls[0]
    assert "event" in msg
    assert call.data["entity_id"] == endpoint.replace("#", ".")
    assert msg["event"]["header"]["name"] == response_type
    assert call.context == context

    return call, msg