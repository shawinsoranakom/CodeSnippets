def test_select_ascii_array(self):
        a = ["awef"]
        b = self._select(a)
        self.assertEqual(a[0], b[0])