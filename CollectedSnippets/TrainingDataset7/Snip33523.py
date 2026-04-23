def test_plain(self):
        output = self.engine.render_to_string("plain", {"a": 1})
        self.assertTrue(
            output.startswith(
                "{&#x27;a&#x27;: 1}"
                "{&#x27;False&#x27;: False, &#x27;None&#x27;: None, "
                "&#x27;True&#x27;: True}\n\n{"
            )
        )