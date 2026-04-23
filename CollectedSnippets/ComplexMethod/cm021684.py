async def test_intent_request_calling_service(alexa_client) -> None:
    """Test a request for calling a service."""
    data = {
        "version": "1.0",
        "session": {
            "new": False,
            "sessionId": SESSION_ID,
            "application": {"applicationId": APPLICATION_ID},
            "attributes": {},
            "user": {"userId": "amzn1.account.AM3B00000000000000000000000"},
        },
        "request": {
            "type": "IntentRequest",
            "requestId": REQUEST_ID,
            "timestamp": "2015-05-13T12:34:56Z",
            "intent": {
                "name": "CallServiceIntent",
                "slots": {"ZodiacSign": {"name": "ZodiacSign", "value": "virgo"}},
            },
        },
    }
    call_count = len(calls)
    req = await _intent_req(alexa_client, data)
    assert req.status == HTTPStatus.OK
    assert call_count + 1 == len(calls)
    call = calls[-1]
    assert call.domain == "test"
    assert call.service == "alexa"
    assert call.data.get("entity_id") == ["switch.test"]
    assert call.data.get("hello") == "virgo"

    data = await req.json()
    assert data["response"]["card"]["title"] == "Card title for virgo"
    assert data["response"]["card"]["content"] == "Card content: virgo"
    assert data["response"]["outputSpeech"]["type"] == "PlainText"
    assert data["response"]["outputSpeech"]["text"] == "Service called for virgo"