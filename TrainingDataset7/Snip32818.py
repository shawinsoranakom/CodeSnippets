def test_backslashes(self):
        self.assertEqual(addslashes(r"\ : backslashes, too"), "\\\\ : backslashes, too")