def test_lambdas(self):
        """Test code with different lambdas produces different hashes."""

        v42 = 42
        v123 = 123

        def f1():
            lambda x: v42

        def f2():
            lambda x: v123

        self.assertNotEqual(get_hash(f1), get_hash(f2))