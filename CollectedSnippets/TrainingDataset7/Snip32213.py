def test_sign_unsign_multiple_keys(self):
        """The default key is a valid verification key."""
        signer = signing.Signer(key="secret", fallback_keys=["oldsecret"])
        signed = signer.sign("abc")
        self.assertEqual(signer.unsign(signed), "abc")