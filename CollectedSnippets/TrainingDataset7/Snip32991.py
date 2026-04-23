def test_newline(self):
        self.assertEqual(linebreaks_filter("line 1\nline 2"), "<p>line 1<br>line 2</p>")