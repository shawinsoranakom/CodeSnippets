def test_ifchanged_param01(self):
        """
        Test one parameter given to ifchanged.
        """
        output = self.engine.render_to_string("ifchanged-param01", {"num": (1, 2, 3)})
        self.assertEqual(output, "..1..2..3")