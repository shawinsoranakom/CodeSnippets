def test_urlize08(self):
        output = self.engine.render_to_string(
            "urlize08", {"a": "Email me at <me@example.com>"}
        )
        self.assertEqual(
            output,
            'Email me at &lt;<a href="mailto:me@example.com">me@example.com</a>&gt;',
        )