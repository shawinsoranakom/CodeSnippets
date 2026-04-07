def test_pbkdf2_upgrade(self):
        hasher = get_hasher("default")
        self.assertEqual("pbkdf2_sha256", hasher.algorithm)
        self.assertNotEqual(hasher.iterations, 1)

        old_iterations = hasher.iterations
        try:
            # Generate a password with 1 iteration.
            hasher.iterations = 1
            encoded = make_password("letmein")
            algo, iterations, salt, hash = encoded.split("$", 3)
            self.assertEqual(iterations, "1")

            state = {"upgraded": False}

            def setter(password):
                state["upgraded"] = True

            # No upgrade is triggered
            self.assertTrue(check_password("letmein", encoded, setter))
            self.assertFalse(state["upgraded"])

            # Revert to the old iteration count and ...
            hasher.iterations = old_iterations

            # ... check if the password would get updated to the new iteration
            # count.
            self.assertTrue(check_password("letmein", encoded, setter))
            self.assertTrue(state["upgraded"])
        finally:
            hasher.iterations = old_iterations