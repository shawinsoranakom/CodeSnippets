def test_hash_funcs_error(self):
        with self.assertRaises(UserHashError):
            get_hash(1, hash_funcs={int: lambda x: "a" + x})