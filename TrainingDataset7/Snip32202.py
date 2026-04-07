def test_invalid_algorithm(self):
        signer = signing.Signer(key="predictable-secret", algorithm="whatever")
        msg = "'whatever' is not an algorithm accepted by the hashlib module."
        with self.assertRaisesMessage(InvalidAlgorithm, msg):
            signer.sign("hello")