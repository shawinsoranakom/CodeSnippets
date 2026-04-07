def test_bcrypt_upgrade(self):
        hasher = get_hasher("bcrypt")
        self.assertEqual("bcrypt", hasher.algorithm)
        self.assertNotEqual(hasher.rounds, 4)

        old_rounds = hasher.rounds
        try:
            # Generate a password with 4 rounds.
            hasher.rounds = 4
            encoded = make_password("letmein", hasher="bcrypt")
            rounds = hasher.safe_summary(encoded)["work factor"]
            self.assertEqual(rounds, 4)

            state = {"upgraded": False}

            def setter(password):
                state["upgraded"] = True

            # No upgrade is triggered.
            self.assertTrue(check_password("letmein", encoded, setter, "bcrypt"))
            self.assertFalse(state["upgraded"])

            # Revert to the old rounds count and ...
            hasher.rounds = old_rounds

            # ... check if the password would get updated to the new count.
            self.assertTrue(check_password("letmein", encoded, setter, "bcrypt"))
            self.assertTrue(state["upgraded"])
        finally:
            hasher.rounds = old_rounds