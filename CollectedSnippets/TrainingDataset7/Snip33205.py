def test_urlize07(self):
        output = self.engine.render_to_string(
            "urlize07", {"a": "Email me at me@example.com"}
        )
        self.assertEqual(
            output,
            'Email me at <a href="mailto:me@example.com">me@example.com</a>',
        )