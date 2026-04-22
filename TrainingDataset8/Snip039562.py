def test_none(self):
        self.assertEqual(get_hash(None), get_hash(None))
        self.assertNotEqual(get_hash(None), get_hash(False))