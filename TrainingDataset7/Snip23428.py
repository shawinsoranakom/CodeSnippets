def test_format_value(self):
        widget = Widget()
        self.assertIsNone(widget.format_value(None))
        self.assertIsNone(widget.format_value(""))
        self.assertEqual(widget.format_value("español"), "español")
        self.assertEqual(widget.format_value(42.5), "42.5")