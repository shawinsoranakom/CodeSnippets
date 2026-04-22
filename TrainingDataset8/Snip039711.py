def test_calculate_file_id(self):
        """Test that file_id generation from data works as expected."""

        fake_bytes = "\x00\x00\xff\x00\x00\xff\x00\x00\xff\x00\x00\xff\x00".encode(
            "utf-8"
        )
        test_hash = "2ba850426b188d25adc5a37ad313080c346f5e88e069e0807d0cdb2b"
        self.assertEqual(test_hash, _calculate_file_id(fake_bytes, "media/any"))

        # Make sure we get different file ids for files with same bytes but diff't mimetypes.
        self.assertNotEqual(
            _calculate_file_id(fake_bytes, "audio/wav"),
            _calculate_file_id(fake_bytes, "video/mp4"),
        )

        # Make sure we get different file ids for files with same bytes and mimetypes but diff't filenames.
        self.assertNotEqual(
            _calculate_file_id(fake_bytes, "audio/wav", filename="name1.wav"),
            _calculate_file_id(fake_bytes, "audio/wav", filename="name2.wav"),
        )