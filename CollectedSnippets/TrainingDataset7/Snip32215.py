def test_default_keys_verification(self):
        old_signer = signing.Signer(key="oldsecret")
        signed = old_signer.sign("abc")
        signer = signing.Signer()
        self.assertEqual(signer.unsign(signed), "abc")