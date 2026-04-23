def test_no_upgrade_on_incorrect_pass(self):
        self.assertEqual("pbkdf2_sha256", get_hasher("default").algorithm)
        for algo in ("pbkdf2_sha1", "md5"):
            with self.subTest(algo=algo):
                encoded = make_password("lètmein", hasher=algo)
                state = {"upgraded": False}

                def setter():
                    state["upgraded"] = True

                self.assertFalse(check_password("WRONG", encoded, setter))
                self.assertFalse(state["upgraded"])