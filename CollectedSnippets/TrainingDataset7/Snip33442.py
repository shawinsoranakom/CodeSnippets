def test_basic_syntax37(self):
        """
        Call methods in the top level of the context.
        """
        output = self.engine.render_to_string(
            "basic-syntax37", {"callable": lambda: "foo bar"}
        )
        self.assertEqual(output, "foo bar")