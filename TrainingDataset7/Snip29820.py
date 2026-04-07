def test_invalid_fields(self):
        msg = "Bloom indexes support a maximum of 32 fields."
        with self.assertRaisesMessage(ValueError, msg):
            BloomIndex(fields=["title"] * 33, name="test_bloom")