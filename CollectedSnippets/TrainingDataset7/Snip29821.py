def test_invalid_columns(self):
        msg = "BloomIndex.columns must be a list or tuple."
        with self.assertRaisesMessage(ValueError, msg):
            BloomIndex(fields=["title"], name="test_bloom", columns="x")
        msg = "BloomIndex.columns cannot have more values than fields."
        with self.assertRaisesMessage(ValueError, msg):
            BloomIndex(fields=["title"], name="test_bloom", columns=[4, 3])