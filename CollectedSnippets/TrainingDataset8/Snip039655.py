def hash_prog_1():
            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)