def test_salted_hmac(self):
        tests = [
            ((b"salt", b"value"), {}, "b51a2e619c43b1ca4f91d15c57455521d71d61eb"),
            (("salt", "value"), {}, "b51a2e619c43b1ca4f91d15c57455521d71d61eb"),
            (
                ("salt", "value"),
                {"secret": "abcdefg"},
                "8bbee04ccddfa24772d1423a0ba43bd0c0e24b76",
            ),
            (
                ("salt", "value"),
                {"secret": "x" * hashlib.sha1().block_size},
                "bd3749347b412b1b0a9ea65220e55767ac8e96b0",
            ),
            (
                ("salt", "value"),
                {"algorithm": "sha256"},
                "ee0bf789e4e009371a5372c90f73fcf17695a8439c9108b0480f14e347b3f9ec",
            ),
            (
                ("salt", "value"),
                {
                    "algorithm": "blake2b",
                    "secret": "x" * hashlib.blake2b().block_size,
                },
                "fc6b9800a584d40732a07fa33fb69c35211269441823bca431a143853c32f"
                "e836cf19ab881689528ede647dac412170cd5d3407b44c6d0f44630690c54"
                "ad3d58",
            ),
        ]
        for args, kwargs, digest in tests:
            with self.subTest(args=args, kwargs=kwargs):
                self.assertEqual(salted_hmac(*args, **kwargs).hexdigest(), digest)