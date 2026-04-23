def test_no_warnings_matched_angle_brackets(self):
        self.assertEqual(check_url_config(None), [])