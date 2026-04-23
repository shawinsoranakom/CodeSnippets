def test_roundtrip(self):
        bytestring = b"foo"
        encoded = urlsafe_base64_encode(bytestring)
        decoded = urlsafe_base64_decode(encoded)
        self.assertEqual(bytestring, decoded)