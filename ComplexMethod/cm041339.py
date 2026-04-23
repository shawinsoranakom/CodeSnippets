def test_aws_trace_logging_contains_payload(self, handler, get_logger):
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
                "input": {"test": "request"},
                "request_headers": {"request": "header"},
                # response
                "output_type": "OutputShape",
                "output": {"test": "response"},
                "response_headers": {"response": "header"},
            },
        )
        log_message = handler.messages[0]
        assert "TestService" in log_message
        assert "RequestShape" in log_message
        assert "OutputShape" in log_message
        assert "{'test': 'request'}" in log_message
        assert "{'test': 'response'}" in log_message

        assert "{'request': 'header'}" in log_message
        assert "{'response': 'header'}" in log_message