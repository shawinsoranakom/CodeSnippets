def test_list_index03(self):
        """
        Fail silently when the list index is out of range.
        """
        output = self.engine.render_to_string("list-index03", {"var": None})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")