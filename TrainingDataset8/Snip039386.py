def test_lambdas_not_hashable(self):
        with self.assertRaises(UnhashableTypeError):
            get_hash(lambda x: x.lower())