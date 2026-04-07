def test_carriage_newline(self):
        self.assertEqual(linebreaksbr("line 1\r\nline 2"), "line 1<br>line 2")