def test_verify_with_non_default_key(self):
        old_signer = signing.Signer(key="secret")
        new_signer = signing.Signer(
            key="newsecret", fallback_keys=["othersecret", "secret"]
        )
        signed = old_signer.sign("abc")
        self.assertEqual(new_signer.unsign(signed), "abc")