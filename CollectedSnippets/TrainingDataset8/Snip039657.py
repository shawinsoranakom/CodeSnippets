def hash_prog_3():
            o = Foo()

            def f():
                return o.get_x()

            return get_hash(f)