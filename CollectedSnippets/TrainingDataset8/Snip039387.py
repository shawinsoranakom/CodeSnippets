def test_generator_not_hashable(self):
        with self.assertRaises(UnhashableTypeError):
            get_hash((x for x in range(1)))