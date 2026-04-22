def test_higher_order(self):
        """Test hashing higher order functions."""

        def f(x):
            def func(v):
                return v**x

            return func

        def g(x):
            def func(v):
                return v * x

            return func

        def h(x):
            def func(v):
                return v**x

            return func

        self.assertNotEqual(get_hash(f), get_hash(g))