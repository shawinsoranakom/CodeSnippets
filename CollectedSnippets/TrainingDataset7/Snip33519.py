def test_cycle30(self):
        """
        A {% with %} tag shouldn't reset the {% cycle %} variable.
        """
        output = self.engine.render_to_string(
            "cycle30", {"irrelevant": 1, "values": [1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 9, 9]}
        )
        self.assertEqual(output, "bcabcabcccaa")