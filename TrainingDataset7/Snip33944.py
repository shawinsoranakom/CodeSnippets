def test_regroup02(self):
        """
        Test for silent failure when target variable isn't found
        """
        output = self.engine.render_to_string("regroup02", {})
        self.assertEqual(output, "")