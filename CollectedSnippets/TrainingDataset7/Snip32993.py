def test_carriage_newline(self):
        self.assertEqual(
            linebreaks_filter("line 1\r\nline 2"), "<p>line 1<br>line 2</p>"
        )