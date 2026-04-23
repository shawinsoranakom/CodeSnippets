def hash_prog_2():
            o = Foo()

            def f():
                return o.get_y()

            return get_hash(f)