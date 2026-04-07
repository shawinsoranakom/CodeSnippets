def test_basic_syntax38(self):
        """
        Call methods returned from dictionary lookups.
        """
        output = self.engine.render_to_string(
            "basic-syntax38", {"var": {"callable": lambda: "foo bar"}}
        )
        self.assertEqual(output, "foo bar")