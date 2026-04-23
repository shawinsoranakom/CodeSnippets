def test_send_catch_log(self):
        test_signal = object()
        handlers_called = set()

        dispatcher.connect(self.error_handler, signal=test_signal)
        dispatcher.connect(self.ok_handler, signal=test_signal)
        with LogCapture() as log:
            result = yield defer.maybeDeferred(
                self._get_result,
                test_signal,
                arg="test",
                handlers_called=handlers_called,
            )

        assert self.error_handler in handlers_called
        assert self.ok_handler in handlers_called
        assert len(log.records) == 1
        record = log.records[0]
        assert "error_handler" in record.getMessage()
        assert record.levelname == "ERROR"
        assert result[0][0] == self.error_handler  # pylint: disable=comparison-with-callable
        assert isinstance(
            result[0][1], Exception if self.returns_exceptions else Failure
        )
        assert result[1] == (self.ok_handler, "OK")

        dispatcher.disconnect(self.error_handler, signal=test_signal)
        dispatcher.disconnect(self.ok_handler, signal=test_signal)