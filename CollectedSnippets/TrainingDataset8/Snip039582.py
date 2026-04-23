def test_non_hashable(self):
        """Test user provided hash functions."""

        g = (x for x in range(1))

        # Unhashable object raises an error
        with self.assertRaises(UnhashableTypeError):
            get_hash(g)

        id_hash_func = {types.GeneratorType: id}

        self.assertEqual(
            get_hash(g, hash_funcs=id_hash_func),
            get_hash(g, hash_funcs=id_hash_func),
        )

        unique_hash_func = {types.GeneratorType: lambda x: time.time()}

        self.assertNotEqual(
            get_hash(g, hash_funcs=unique_hash_func),
            get_hash(g, hash_funcs=unique_hash_func),
        )