def _test_scrypt_upgrade(self, attr, summary_key, new_value):
        hasher = get_hasher("scrypt")
        self.assertEqual(hasher.algorithm, "scrypt")
        self.assertNotEqual(getattr(hasher, attr), new_value)

        old_value = getattr(hasher, attr)
        try:
            # Generate hash with attr set to the new value.
            setattr(hasher, attr, new_value)
            encoded = make_password("lètmein", "seasalt", "scrypt")
            attr_value = hasher.safe_summary(encoded)[summary_key]
            self.assertEqual(attr_value, new_value)

            state = {"upgraded": False}

            def setter(password):
                state["upgraded"] = True

            # No update is triggered.
            self.assertIs(check_password("lètmein", encoded, setter, "scrypt"), True)
            self.assertIs(state["upgraded"], False)
            # Revert to the old value.
            setattr(hasher, attr, old_value)
            # Password is updated.
            self.assertIs(check_password("lètmein", encoded, setter, "scrypt"), True)
            self.assertIs(state["upgraded"], True)
        finally:
            setattr(hasher, attr, old_value)