def test_create_api_message_defaults(hass: HomeAssistant) -> None:
    """Create an API message response of a request with defaults."""
    request = get_new_request("Alexa.PowerController", "TurnOn", "switch#xy")
    directive_header = request["directive"]["header"]
    directive = state_report.AlexaDirective(request)

    msg = directive.response(payload={"test": 3})._response

    assert "event" in msg
    msg = msg["event"]

    assert msg["header"]["messageId"] is not None
    assert msg["header"]["messageId"] != directive_header["messageId"]
    assert msg["header"]["correlationToken"] == directive_header["correlationToken"]
    assert msg["header"]["name"] == "Response"
    assert msg["header"]["namespace"] == "Alexa"
    assert msg["header"]["payloadVersion"] == "3"

    assert "test" in msg["payload"]
    assert msg["payload"]["test"] == 3

    assert msg["endpoint"] == request["directive"]["endpoint"]
    assert msg["endpoint"] is not request["directive"]["endpoint"]