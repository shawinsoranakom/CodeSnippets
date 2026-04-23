def test_invalid_columns_value(self):
        msg = "BloomIndex.columns must contain integers from 1 to 4095."
        for length in (0, 4096):
            with self.subTest(length), self.assertRaisesMessage(ValueError, msg):
                BloomIndex(fields=["title"], name="test_bloom", columns=[length])