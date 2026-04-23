def test_aws_trace_logging_replaces_bigger_blobs(self, handler, get_logger):
        logger = get_logger(handler)
        logger.info(
            "AWS %s.%s => %s",
            "TestService",
            "Operation",
            "201",
            extra={
                # context
                "account_id": "123123123123",
                "region": "invalid-region",
                # request
                "input_type": "RequestShape",
                "input": {"request": b"a" * 1024},
                "request_headers": {"request": "header"},
                # response
                "output_type": "OutputShape",
                "output": {"response": b"a" * 1025},
                "response_headers": {"response": "header"},
            },
        )
        log_message = handler.messages[0]
        assert "TestService" in log_message
        assert "RequestShape" in log_message
        assert "OutputShape" in log_message
        assert "{'request': 'Bytes(1.024KB)'}" in log_message
        assert "{'response': 'Bytes(1.025KB)'}" in log_message

        assert "{'request': 'header'}" in log_message
        assert "{'response': 'header'}" in log_message