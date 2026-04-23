def test_non_hashable(self):
        """Test the hash of functions that return non hashable objects."""

        gen = (x for x in range(1))

        def f(x):
            return gen

        def g(y):
            return gen

        with self.assertRaises(UnhashableTypeError):
            get_hash(gen)

        hash_funcs = {types.GeneratorType: id}

        self.assertEqual(
            get_hash(f, hash_funcs=hash_funcs), get_hash(g, hash_funcs=hash_funcs)
        )