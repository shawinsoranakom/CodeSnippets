def test_dict(self):
        self.assertEqual(get_hash({1: 1}), get_hash({1: 1}))
        self.assertNotEqual(get_hash({1: 1}), get_hash({1: 2}))
        self.assertNotEqual(get_hash({1: 1}), get_hash([(1, 1)]))

        dict_gen = {1: (x for x in range(1))}
        with self.assertRaises(UnhashableTypeError):
            get_hash(dict_gen)