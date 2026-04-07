def test_no_args(self):
        self.assertEqual(time_filter(""), "")
        self.assertEqual(time_filter(None), "")