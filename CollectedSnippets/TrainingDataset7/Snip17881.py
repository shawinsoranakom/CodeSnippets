def test_upgrade(self):
        self.assertEqual("pbkdf2_sha256", get_hasher("default").algorithm)
        for algo in ("pbkdf2_sha1", "md5"):
            with self.subTest(algo=algo):
                encoded = make_password("lètmein", hasher=algo)
                state = {"upgraded": False}

                def setter(password):
                    state["upgraded"] = True

                self.assertTrue(check_password("lètmein", encoded, setter))
                self.assertTrue(state["upgraded"])