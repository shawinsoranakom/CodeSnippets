def test_basic_syntax29(self):
        output = self.engine.render_to_string(
            "basic-syntax29", {"a": SilentAttrClass()}
        )
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")