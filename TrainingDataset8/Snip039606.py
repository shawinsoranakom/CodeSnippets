def test_decorated(self):
        """Test decorated functions."""

        def do(func):
            @functools.wraps(func)
            def wrapper_do(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper_do

        @do
        def f():
            return 42

        @do
        def g():
            return 12

        @do
        def h():
            return 42

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))