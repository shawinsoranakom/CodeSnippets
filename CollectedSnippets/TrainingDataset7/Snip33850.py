def test_list_index05(self):
        """
        Dictionary lookup wins out when dict's key is a string.
        """
        output = self.engine.render_to_string("list-index05", {"var": {"1": "hello"}})
        self.assertEqual(output, "hello")