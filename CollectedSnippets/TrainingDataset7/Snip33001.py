def test_carriage(self):
        self.assertEqual(linebreaksbr("line 1\rline 2"), "line 1<br>line 2")