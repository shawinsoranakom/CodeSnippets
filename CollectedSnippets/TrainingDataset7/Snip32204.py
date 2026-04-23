def test_sign_unsign_non_string(self):
        signer = signing.Signer(key="predictable-secret")
        values = [
            123,
            1.23,
            True,
            datetime.date.today(),
        ]
        for value in values:
            with self.subTest(value):
                signed = signer.sign(value)
                self.assertIsInstance(signed, str)
                self.assertNotEqual(signed, value)
                self.assertEqual(signer.unsign(signed), str(value))