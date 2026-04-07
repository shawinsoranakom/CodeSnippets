def assertLogRecord(self, handler, expected):
        handler.stream.seek(0)
        self.assertEqual(handler.stream.read().strip(), expected)