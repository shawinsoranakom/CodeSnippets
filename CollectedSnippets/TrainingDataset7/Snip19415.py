def test_insecure_secret_key_fallbacks(self):
        self.assertEqual(
            base.check_secret_key_fallbacks(None),
            [
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[0]", id=base.W025.id),
            ],
        )