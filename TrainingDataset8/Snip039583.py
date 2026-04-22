def test_override_streamlit_hash_func(self):
        """Test that a user provided hash function has priority over a streamlit one."""

        hash_funcs = {int: lambda x: "hello"}
        self.assertNotEqual(get_hash(1), get_hash(1, hash_funcs=hash_funcs))