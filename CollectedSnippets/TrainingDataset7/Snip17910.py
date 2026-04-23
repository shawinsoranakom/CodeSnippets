def _test_argon2_upgrade(self, attr, summary_key, new_value):
        hasher = get_hasher("argon2")
        self.assertEqual("argon2", hasher.algorithm)
        self.assertNotEqual(getattr(hasher, attr), new_value)

        old_value = getattr(hasher, attr)
        try:
            # Generate hash with attr set to 1
            setattr(hasher, attr, new_value)
            encoded = make_password("letmein", hasher="argon2")
            attr_value = hasher.safe_summary(encoded)[summary_key]
            self.assertEqual(attr_value, new_value)

            state = {"upgraded": False}

            def setter(password):
                state["upgraded"] = True

            # No upgrade is triggered.
            self.assertTrue(check_password("letmein", encoded, setter, "argon2"))
            self.assertFalse(state["upgraded"])

            # Revert to the old rounds count and ...
            setattr(hasher, attr, old_value)

            # ... check if the password would get updated to the new count.
            self.assertTrue(check_password("letmein", encoded, setter, "argon2"))
            self.assertTrue(state["upgraded"])
        finally:
            setattr(hasher, attr, old_value)