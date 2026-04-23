def test_multiple_keys(self):
        self.assertEqual(
            base.check_secret_key_fallbacks(None),
            [
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[1]", id=base.W025.id),
            ],
        )