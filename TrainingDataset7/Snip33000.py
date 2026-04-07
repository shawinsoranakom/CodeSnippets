def test_newline(self):
        self.assertEqual(linebreaksbr("line 1\nline 2"), "line 1<br>line 2")