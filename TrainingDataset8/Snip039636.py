def hash_prog_2():
            x = 42

            def g():
                return x

            def f():
                return g()

            return get_hash(f)