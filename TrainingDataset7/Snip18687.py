def test_select_unicode_array(self):
        a = ["ᄲawef"]
        b = self._select(a)
        self.assertEqual(a[0], b[0])