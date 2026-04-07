def test_ifchanged_else01(self):
        """
        Test the else clause of ifchanged.
        """
        output = self.engine.render_to_string(
            "ifchanged-else01", {"ids": [1, 1, 2, 2, 2, 3]}
        )
        self.assertEqual(output, "1-first,1-other,2-first,2-other,2-other,3-first,")