def test_inputs(self):
        self.assertEqual(time_filter(time(13), "h"), "01")
        self.assertEqual(time_filter(time(0), "h"), "12")