def test_referenced_referenced(self):
        """Test that we can follow references."""

        def hash_prog_1():
            x = 12

            def g():
                return x

            def f():
                return g()

            return get_hash(f)

        def hash_prog_2():
            x = 42

            def g():
                return x

            def f():
                return g()

            return get_hash(f)

        self.assertNotEqual(hash_prog_1(), hash_prog_2())