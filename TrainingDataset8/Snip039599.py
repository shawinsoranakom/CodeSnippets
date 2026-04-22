def test_dict_reference(self):
        """Test code with lambdas that call a dictionary."""

        a = {"foo": 42, "bar": {"baz": 12}}

        def f():
            return a["bar"]["baz"]

        def g():
            return a["foo"]

        def h():
            return a["bar"]["baz"]

        self.assertNotEqual(get_hash(f), get_hash(g))
        self.assertEqual(get_hash(f), get_hash(h))