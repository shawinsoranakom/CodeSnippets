def test_inheritance14(self):
        """
        A block defined only in a child template shouldn't be displayed
        """
        output = self.engine.render_to_string("inheritance14")
        self.assertEqual(output, "1&3_")