def test_signature(self):
        "signature() method should generate a signature"
        signer = signing.Signer(key="predictable-secret")
        signer2 = signing.Signer(key="predictable-secret2")
        for s in (
            b"hello",
            b"3098247:529:087:",
            "\u2019".encode(),
        ):
            self.assertEqual(
                signer.signature(s),
                signing.base64_hmac(
                    signer.salt + "signer",
                    s,
                    "predictable-secret",
                    algorithm=signer.algorithm,
                ),
            )
            self.assertNotEqual(signer.signature(s), signer2.signature(s))