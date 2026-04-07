def test_escapejs02(self):
        output = self.engine.render_to_string(
            "escapejs02", {"a": "testing\r\njavascript 'string\" <b>escaping</b>"}
        )
        self.assertEqual(
            output,
            "testing\\u000D\\u000Ajavascript "
            "\\u0027string\\u0022 \\u003Cb\\u003E"
            "escaping\\u003C/b\\u003E",
        )