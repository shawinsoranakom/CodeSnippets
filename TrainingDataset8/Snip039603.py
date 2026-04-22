def test_class_referenced(self):
        """Test hash for classes with methods that reference values."""

        def hash_prog_1():
            class Foo:
                x = 12

                def get_x(self):
                    return self.x

            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)

        def hash_prog_2():
            class Foo:
                x = 42

                def get_x(self):
                    return self.x

            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)

        self.assertNotEqual(hash_prog_1(), hash_prog_2())