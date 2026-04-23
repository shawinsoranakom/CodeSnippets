def test_default_hmac_alg(self):
        kwargs = {
            "password": b"password",
            "salt": b"salt",
            "iterations": 1,
            "dklen": 20,
        }
        self.assertEqual(
            pbkdf2(**kwargs),
            hashlib.pbkdf2_hmac(hash_name=hashlib.sha256().name, **kwargs),
        )