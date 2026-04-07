def test_decode_detects_tampering(self):
        "loads should raise exception for tampered objects"
        transforms = (
            lambda s: s.upper(),
            lambda s: s + "a",
            lambda s: "a" + s[1:],
            lambda s: s.replace(":", ""),
        )
        value = {
            "foo": "bar",
            "baz": 1,
        }
        encoded = signing.dumps(value)
        self.assertEqual(value, signing.loads(encoded))
        for transform in transforms:
            with self.assertRaises(signing.BadSignature):
                signing.loads(transform(encoded))