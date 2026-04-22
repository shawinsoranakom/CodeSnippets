def hash_prog_2():
            class Foo:
                x = 42

                def get_x(self):
                    return self.x

            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)