def test_reference_msg(self):
        """Test creation of 'reference' ForwardMsgs"""
        msg = _create_dataframe_msg([1, 2, 3], 34)
        ref_msg = create_reference_msg(msg)
        self.assertEqual(populate_hash_if_needed(msg), ref_msg.ref_hash)
        self.assertEqual(msg.metadata, ref_msg.metadata)