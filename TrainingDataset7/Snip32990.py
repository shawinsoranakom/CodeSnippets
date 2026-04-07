def test_line(self):
        self.assertEqual(linebreaks_filter("line 1"), "<p>line 1</p>")