def test_decode_serializer_exception(self):
        signer = TimestampSigner(salt=self.session.key_salt)
        encoded = signer.sign(b"invalid data")
        self.assertEqual(self.session.decode(encoded), {})