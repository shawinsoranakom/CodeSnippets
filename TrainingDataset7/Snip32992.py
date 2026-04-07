def test_carriage(self):
        self.assertEqual(linebreaks_filter("line 1\rline 2"), "<p>line 1<br>line 2</p>")