def test_format_value(self):
        widget = self.widget(choices=self.numeric_choices)
        self.assertEqual(widget.format_value(None), [])
        self.assertEqual(widget.format_value(""), [""])
        self.assertEqual(widget.format_value([3, 0, 1]), ["3", "0", "1"])