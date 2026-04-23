def assert_sending_requests(
    signal_requests_mock_factory: Mocker,
    attachments_num: int = 0,
    recipients: list[str] | None = None,
) -> None:
    """Assert message was send with correct parameters."""
    send_request = signal_requests_mock_factory.request_history[-1]
    assert send_request.path == SIGNAL_SEND_PATH_SUFIX

    body_request = json.loads(send_request.text)
    assert body_request["message"] == MESSAGE
    assert body_request["number"] == NUMBER_FROM
    assert body_request["recipients"] == (recipients or NUMBERS_TO)
    assert len(body_request["base64_attachments"]) == attachments_num

    for attachment in body_request["base64_attachments"]:
        if len(attachment) > 0:
            assert base64.b64decode(attachment) == CONTENT