def test_extra_fields(self, log_output):
        logger, string_io = log_output

        logger.info('Test message', extra={'key': '..val..'})
        output = json.loads(string_io.getvalue())
        assert output['key'] == '..val..'
        assert output['message'] == 'Test message'
        assert output['severity'] == 'INFO'
        assert output['ts'] == FROZEN_TIMESTAMP
        assert output['module'] == 'test_logger'
        assert output['funcName'] == 'test_extra_fields'
        assert 'lineno' in output