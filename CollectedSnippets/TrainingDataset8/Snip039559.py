def test_internal_hashing_error(self):
        def side_effect(i):
            if i == 123456789:
                return "a" + 1
            return i.to_bytes((i.bit_length() + 8) // 8, "little", signed=True)

        with self.assertRaises(InternalHashError):
            with patch(
                "streamlit.runtime.legacy_caching.hashing._int_to_bytes",
                side_effect=side_effect,
            ):
                get_hash(123456789)