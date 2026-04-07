def test_signature_with_salt(self):
        signer = signing.Signer(key="predictable-secret", salt="extra-salt")
        self.assertEqual(
            signer.signature("hello"),
            signing.base64_hmac(
                "extra-salt" + "signer",
                "hello",
                "predictable-secret",
                algorithm=signer.algorithm,
            ),
        )
        self.assertNotEqual(
            signing.Signer(key="predictable-secret", salt="one").signature("hello"),
            signing.Signer(key="predictable-secret", salt="two").signature("hello"),
        )