def hash_prog_2():
            df = pd.DataFrame({"foo": [42]})

            def f():
                return df

            return get_hash(f)