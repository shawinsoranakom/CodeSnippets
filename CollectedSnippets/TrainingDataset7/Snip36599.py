def test_empty(self):
        self.assertEqual(nformat("", "."), "")
        self.assertEqual(nformat(None, "."), "None")