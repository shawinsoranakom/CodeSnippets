def test_scrypt(self):
        encoded = make_password("lètmein", "seasalt", "scrypt")
        self.assertEqual(
            encoded,
            "scrypt$16384$seasalt$8$5$ECMIUp+LMxMSK8xB/IVyba+KYGTI7FTnet025q/1f"
            "/vBAVnnP3hdYqJuRi+mJn6ji6ze3Fbb7JEFPKGpuEf5vw==",
        )
        self.assertIs(is_password_usable(encoded), True)
        self.assertIs(check_password("lètmein", encoded), True)
        self.assertIs(check_password("lètmeinz", encoded), False)
        self.assertEqual(identify_hasher(encoded).algorithm, "scrypt")
        # Blank passwords.
        blank_encoded = make_password("", "seasalt", "scrypt")
        self.assertIs(blank_encoded.startswith("scrypt$"), True)
        self.assertIs(is_password_usable(blank_encoded), True)
        self.assertIs(check_password("", blank_encoded), True)
        self.assertIs(check_password(" ", blank_encoded), False)