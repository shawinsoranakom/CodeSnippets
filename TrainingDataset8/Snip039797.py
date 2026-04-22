def test_should_limit_msg_size(self):
        max_message_size_mb = 50

        runtime_util._max_message_size_bytes = None  # Reset cached value
        with patch_config_options({"server.maxMessageSize": max_message_size_mb}):
            # Set up a larger than limit ForwardMsg string
            large_msg = create_dataframe_msg([1, 2, 3])
            large_msg.delta.new_element.markdown.body = (
                "X" * (max_message_size_mb + 10) * 1000 * 1000
            )
            # Create a copy, since serialize_forward_msg modifies the original proto
            large_msg_copy = ForwardMsg()
            large_msg_copy.CopyFrom(large_msg)
            deserialized_msg = ForwardMsg()
            deserialized_msg.ParseFromString(serialize_forward_msg(large_msg_copy))

            # The metadata should be the same, but contents should be replaced
            self.assertEqual(deserialized_msg.metadata, large_msg.metadata)
            self.assertNotEqual(deserialized_msg, large_msg)
            self.assertTrue(
                "exceeds the message size limit"
                in deserialized_msg.delta.new_element.exception.message
            )