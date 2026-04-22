def foo(arg):
            # Reference the generator object. It will be hashed when we
            # hash the function body to generate foo's cache_key.
            print(dict_gen)
            return []