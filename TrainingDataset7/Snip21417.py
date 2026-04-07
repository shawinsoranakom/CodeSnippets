def test_equal(self):
        f = F("name")
        same_f = F("name")
        other_f = F("username")
        self.assertEqual(f, same_f)
        self.assertNotEqual(f, other_f)