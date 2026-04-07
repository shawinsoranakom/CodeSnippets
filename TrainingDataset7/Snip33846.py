def test_list_index01(self):
        """
        List-index syntax allows a template to access a certain item of a
        subscriptable object.
        """
        output = self.engine.render_to_string(
            "list-index01", {"var": ["first item", "second item"]}
        )
        self.assertEqual(output, "second item")