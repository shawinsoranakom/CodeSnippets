def test_lambdas_calls(self):
        """Test code with lambdas that call functions."""

        def f_lower():
            lambda x: x.lower()

        def f_upper():
            lambda x: x.upper()

        def f_lower2():
            lambda x: x.lower()

        self.assertNotEqual(get_hash(f_lower), get_hash(f_upper))
        self.assertEqual(get_hash(f_lower), get_hash(f_lower2))