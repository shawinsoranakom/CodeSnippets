def test_bool(self):
        self.assertEqual(get_hash(True), get_hash(True))
        self.assertNotEqual(get_hash(True), get_hash(False))