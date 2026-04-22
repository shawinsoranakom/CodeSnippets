def bad_hash_func(x):
            x += 10  # Throws a TypeError since x has type MyObj.
            return x