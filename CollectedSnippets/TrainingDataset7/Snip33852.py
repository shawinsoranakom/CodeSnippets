def test_list_index07(self):
        """
        Dictionary lookup wins out when there is a string and int version
        of the key.
        """
        output = self.engine.render_to_string(
            "list-index07", {"var": {"1": "hello", 1: "world"}}
        )
        self.assertEqual(output, "hello")