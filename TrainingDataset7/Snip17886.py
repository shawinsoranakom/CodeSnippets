def test_pbkdf2_upgrade_new_hasher(self):
        hasher = get_hasher("default")
        self.assertEqual("pbkdf2_sha256", hasher.algorithm)
        self.assertNotEqual(hasher.iterations, 1)

        state = {"upgraded": False}

        def setter(password):
            state["upgraded"] = True

        with self.settings(
            PASSWORD_HASHERS=["auth_tests.test_hashers.PBKDF2SingleIterationHasher"]
        ):
            encoded = make_password("letmein")
            algo, iterations, salt, hash = encoded.split("$", 3)
            self.assertEqual(iterations, "1")

            # No upgrade is triggered
            self.assertTrue(check_password("letmein", encoded, setter))
            self.assertFalse(state["upgraded"])

        # Revert to the old iteration count and check if the password would get
        # updated to the new iteration count.
        with self.settings(
            PASSWORD_HASHERS=[
                "django.contrib.auth.hashers.PBKDF2PasswordHasher",
                "auth_tests.test_hashers.PBKDF2SingleIterationHasher",
            ]
        ):
            self.assertTrue(check_password("letmein", encoded, setter))
            self.assertTrue(state["upgraded"])