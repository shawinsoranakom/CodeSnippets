def test_message_only(self):
        reporter = ExceptionReporter(None, None, "I'm a little teapot", None)
        reporter.get_traceback_text()