def test_msg_hash(self):
        """Test that ForwardMsg hash generation works as expected"""
        msg1 = _create_dataframe_msg([1, 2, 3])
        msg2 = _create_dataframe_msg([1, 2, 3])
        self.assertEqual(populate_hash_if_needed(msg1), populate_hash_if_needed(msg2))

        msg3 = _create_dataframe_msg([2, 3, 4])
        self.assertNotEqual(
            populate_hash_if_needed(msg1), populate_hash_if_needed(msg3)
        )