def hash_prog_3():
            df = pd.DataFrame({"foo": [12]})

            def f():
                return df

            return get_hash(f)