def test_list_index02(self):
        """
        Fail silently when the list index is out of range.
        """
        output = self.engine.render_to_string(
            "list-index02", {"var": ["first item", "second item"]}
        )
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")