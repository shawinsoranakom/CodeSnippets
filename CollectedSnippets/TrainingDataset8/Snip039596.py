def test_pandas_df(self):
        """Test code that references pandas dataframes."""

        def hash_prog_1():
            df = pd.DataFrame({"foo": [12]})

            def f():
                return df

            return get_hash(f)

        def hash_prog_2():
            df = pd.DataFrame({"foo": [42]})

            def f():
                return df

            return get_hash(f)

        def hash_prog_3():
            df = pd.DataFrame({"foo": [12]})

            def f():
                return df

            return get_hash(f)

        self.assertNotEqual(hash_prog_1(), hash_prog_2())
        self.assertEqual(hash_prog_1(), hash_prog_3())