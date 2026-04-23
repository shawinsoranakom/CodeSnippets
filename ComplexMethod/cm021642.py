def test_create_api_message_special() -> None:
    """Create an API message response of a request with non defaults."""
    request = get_new_request("Alexa.PowerController", "TurnOn")
    directive_header = request["directive"]["header"]
    directive_header.pop("correlationToken")
    directive = state_report.AlexaDirective(request)

    msg = directive.response("testName", "testNameSpace")._response

    assert "event" in msg
    msg = msg["event"]

    assert msg["header"]["messageId"] is not None
    assert msg["header"]["messageId"] != directive_header["messageId"]
    assert "correlationToken" not in msg["header"]
    assert msg["header"]["name"] == "testName"
    assert msg["header"]["namespace"] == "testNameSpace"
    assert msg["header"]["payloadVersion"] == "3"

    assert msg["payload"] == {}
    assert "endpoint" not in msg