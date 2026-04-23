def test_ending_with_dollar(self):
        result = check_url_config(None)
        self.assertEqual(len(result), 1)
        warning = result[0]
        self.assertEqual(warning.id, "2_0.W001")
        expected_msg = "Your URL pattern 'ending-with-dollar$' has a route"
        self.assertIn(expected_msg, warning.msg)