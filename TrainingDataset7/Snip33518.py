def test_cycle29(self):
        """
        A named {% cycle %} tag works inside an {% ifchanged %} block and a
        {% for %} loop.
        """
        output = self.engine.render_to_string(
            "cycle29", {"values": [1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 9, 9]}
        )
        self.assertEqual(output, "bcabcabcccaa")