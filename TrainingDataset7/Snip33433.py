def test_basic_syntax28(self):
        output = self.engine.render_to_string(
            "basic-syntax28", {"a": SilentGetItemClass()}
        )
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")