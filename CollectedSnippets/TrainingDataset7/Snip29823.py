def test_invalid_length(self):
        msg = "BloomIndex.length must be None or an integer from 1 to 4096."
        for length in (0, 4097):
            with self.subTest(length), self.assertRaisesMessage(ValueError, msg):
                BloomIndex(fields=["title"], name="test_bloom", length=length)