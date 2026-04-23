def test_generator(self):
        with self.assertRaises(UnhashableTypeError):
            get_hash((x for x in range(1)))