def test_delta_metadata(self):
        """Test that delta metadata doesn't change the hash"""
        msg1 = _create_dataframe_msg([1, 2, 3], 1)
        msg2 = _create_dataframe_msg([1, 2, 3], 2)
        self.assertEqual(populate_hash_if_needed(msg1), populate_hash_if_needed(msg2))