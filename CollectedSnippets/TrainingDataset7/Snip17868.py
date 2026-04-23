def test_md5(self):
        encoded = make_password("lètmein", "seasalt", "md5")
        self.assertEqual(encoded, "md5$seasalt$3f86d0d3d465b7b458c231bf3555c0e3")
        self.assertTrue(is_password_usable(encoded))
        self.assertTrue(check_password("lètmein", encoded))
        self.assertFalse(check_password("lètmeinz", encoded))
        self.assertEqual(identify_hasher(encoded).algorithm, "md5")
        # Blank passwords
        blank_encoded = make_password("", "seasalt", "md5")
        self.assertTrue(blank_encoded.startswith("md5$"))
        self.assertTrue(is_password_usable(blank_encoded))
        self.assertTrue(check_password("", blank_encoded))
        self.assertFalse(check_password(" ", blank_encoded))
        # Salt entropy check.
        hasher = get_hasher("md5")
        encoded_weak_salt = make_password("lètmein", "iodizedsalt", "md5")
        encoded_strong_salt = make_password("lètmein", hasher.salt(), "md5")
        self.assertIs(hasher.must_update(encoded_weak_salt), True)
        self.assertIs(hasher.must_update(encoded_strong_salt), False)