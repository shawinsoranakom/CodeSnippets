def test_tuple(self):
        self.assertEqual(get_hash((1, 2)), get_hash((1, 2)))
        self.assertNotEqual(get_hash((1, 2)), get_hash((2, 2)))
        self.assertNotEqual(get_hash((1,)), get_hash(1))
        self.assertNotEqual(get_hash((1,)), get_hash([1]))