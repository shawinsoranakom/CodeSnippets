def test_int(self):
        self.assertEqual(get_hash(145757624235), get_hash(145757624235))
        self.assertNotEqual(get_hash(10), get_hash(11))
        self.assertNotEqual(get_hash(-1), get_hash(1))
        self.assertNotEqual(get_hash(2**7), get_hash(2**7 - 1))
        self.assertNotEqual(get_hash(2**7), get_hash(2**7 + 1))