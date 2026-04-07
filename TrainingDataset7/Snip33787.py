def test_ifchanged_param03(self):
        """
        Test multiple parameters to ifchanged.
        """
        output = self.engine.render_to_string(
            "ifchanged-param03", {"num": (1, 1, 2), "numx": (5, 6, 6)}
        )
        self.assertEqual(output, "156156256")