def test_unescape_string_literal_invalid_value(self):
        items = ["", "abc", "'abc\""]
        for item in items:
            msg = f"Not a string literal: {item!r}"
            with self.assertRaisesMessage(ValueError, msg):
                text.unescape_string_literal(item)