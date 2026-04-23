def test_sign_unsign_ignore_secret_key_fallbacks(self):
        old_signer = signing.Signer(key="oldsecret")
        signed = old_signer.sign("abc")
        signer = signing.Signer(fallback_keys=[])
        with self.assertRaises(signing.BadSignature):
            signer.unsign(signed)