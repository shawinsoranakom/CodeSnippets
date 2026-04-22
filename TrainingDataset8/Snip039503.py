def test_hash_funcs_acceptable_keys(self):
        @st.cache
        def unhashable_type_func():
            return (x for x in range(1))

        @st.cache(hash_funcs={types.GeneratorType: id})
        def hf_key_as_type():
            return (x for x in range(1))

        @st.cache(hash_funcs={"builtins.generator": id})
        def hf_key_as_str():
            return (x for x in range(1))

        with self.assertRaises(hashing.UnhashableTypeError) as cm:
            unhashable_type_func()

        self.assertEqual(list(hf_key_as_type()), list(hf_key_as_str()))