def test_widthratio11(self):
        """
        #10043: widthratio should allow max_width to be a variable
        """
        output = self.engine.render_to_string(
            "widthratio11", {"a": 50, "c": 100, "b": 100}
        )
        self.assertEqual(output, "50")