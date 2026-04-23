def test_list_index04(self):
        """
        Fail silently when variable is a dict without the specified key.
        """
        output = self.engine.render_to_string("list-index04", {"var": {}})
        if self.engine.string_if_invalid:
            self.assertEqual(output, "INVALID")
        else:
            self.assertEqual(output, "")