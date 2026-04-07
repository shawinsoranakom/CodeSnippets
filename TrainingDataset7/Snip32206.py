def test_sign_unsign_object(self):
        signer = signing.Signer(key="predictable-secret")
        tests = [
            ["a", "list"],
            "a string \u2019",
            {"a": "dictionary"},
        ]
        for obj in tests:
            with self.subTest(obj=obj):
                signed_obj = signer.sign_object(obj)
                self.assertNotEqual(obj, signed_obj)
                self.assertEqual(obj, signer.unsign_object(signed_obj))
                signed_obj = signer.sign_object(obj, compress=True)
                self.assertNotEqual(obj, signed_obj)
                self.assertEqual(obj, signer.unsign_object(signed_obj))