def test_works_with_non_ascii_keys(self):
        binary_key = b"\xe7"  # Set some binary (non-ASCII key)

        s = signing.Signer(key=binary_key)
        self.assertEqual(
            "foo:EE4qGC5MEKyQG5msxYA0sBohAxLC0BJf8uRhemh0BGU",
            s.sign("foo"),
        )