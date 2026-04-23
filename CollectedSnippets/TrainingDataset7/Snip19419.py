def test_multiple_bad_keys(self):
        self.assertEqual(
            base.check_secret_key_fallbacks(None),
            [
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[1]", id=base.W025.id),
                Warning(base.W025.msg % "SECRET_KEY_FALLBACKS[2]", id=base.W025.id),
            ],
        )