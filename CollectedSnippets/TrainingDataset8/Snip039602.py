def test_class(self):
        """Test hash for classes if we call different functions."""

        x = 12
        y = 13

        class Foo:
            def get_x(self):
                return x

            def get_y(self):
                return y

        def hash_prog_1():
            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)

        def hash_prog_2():
            o = Foo()

            def f():
                return o.get_y()

            return get_hash(f)

        def hash_prog_3():
            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)

        self.assertNotEqual(hash_prog_1(), hash_prog_2())
        self.assertEqual(hash_prog_1(), hash_prog_3())