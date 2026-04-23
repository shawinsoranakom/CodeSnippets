def test_bad_algorithm(self):
        msg = (
            "Unknown password hashing algorithm '%s'. Did you specify it in "
            "the PASSWORD_HASHERS setting?"
        )
        with self.assertRaisesMessage(ValueError, msg % "lolcat"):
            make_password("lètmein", hasher="lolcat")
        with self.assertRaisesMessage(ValueError, msg % "lolcat"):
            identify_hasher("lolcat$salt$hash")