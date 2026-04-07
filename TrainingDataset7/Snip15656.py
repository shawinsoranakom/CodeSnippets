def assertOutput(self, stream, msg, regex=False):
        "Utility assertion: assert that the given message exists in the output"
        if regex:
            self.assertIsNotNone(
                re.search(msg, stream),
                "'%s' does not match actual output text '%s'" % (msg, stream),
            )
        else:
            self.assertIn(
                msg,
                stream,
                "'%s' does not match actual output text '%s'" % (msg, stream),
            )