def test_list_index06(self):
        """
        But list-index lookup wins out when dict's key is an int, which
        behind the scenes is really a dictionary lookup (for a dict)
        after converting the key to an int.
        """
        output = self.engine.render_to_string("list-index06", {"var": {1: "hello"}})
        self.assertEqual(output, "hello")