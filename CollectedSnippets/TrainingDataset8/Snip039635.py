def hash_prog_1():
            x = 12

            def g():
                return x

            def f():
                return g()

            return get_hash(f)