def test_sign_unsign(self):
        "sign/unsign should be reversible"
        signer = signing.Signer(key="predictable-secret")
        examples = [
            "q;wjmbk;wkmb",
            "3098247529087",
            "3098247:529:087:",
            "jkw osanteuh ,rcuh nthu aou oauh ,ud du",
            "\u2019",
        ]
        for example in examples:
            signed = signer.sign(example)
            self.assertIsInstance(signed, str)
            self.assertNotEqual(example, signed)
            self.assertEqual(example, signer.unsign(signed))