def test_cache16(self):
        """
        Regression test for #7460.
        """
        output = self.engine.render_to_string(
            "cache16", {"foo": "foo", "bar": "with spaces"}
        )
        self.assertEqual(output, "")