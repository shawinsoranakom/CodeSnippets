def test_unsign_detects_tampering(self):
        "unsign should raise an exception if the value has been tampered with"
        signer = signing.Signer(key="predictable-secret")
        value = "Another string"
        signed_value = signer.sign(value)
        transforms = (
            lambda s: s.upper(),
            lambda s: s + "a",
            lambda s: "a" + s[1:],
            lambda s: s.replace(":", ""),
        )
        self.assertEqual(value, signer.unsign(signed_value))
        for transform in transforms:
            with self.assertRaises(signing.BadSignature):
                signer.unsign(transform(signed_value))