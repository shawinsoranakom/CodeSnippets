def test_sqlalchemy_engine(self, dialect, password_key):
        def connect():
            pass

        url = "%s://localhost/db" % dialect
        auth_url = "%s://user:pass@localhost/db" % dialect

        self.assertEqual(hash_engine(url), hash_engine(url))
        self.assertEqual(
            hash_engine(auth_url, creator=connect),
            hash_engine(auth_url, creator=connect),
        )

        # Note: Hashing an engine with a creator can only be equal to the hash of another
        # engine with a creator, even if the underlying connection arguments are the same
        self.assertNotEqual(hash_engine(url), hash_engine(url, creator=connect))

        self.assertNotEqual(hash_engine(url), hash_engine(auth_url))
        self.assertNotEqual(
            hash_engine(url, encoding="utf-8"), hash_engine(url, encoding="ascii")
        )
        self.assertNotEqual(
            hash_engine(url, creator=connect), hash_engine(url, creator=lambda: True)
        )

        # mssql doesn't use `connect_args`
        if dialect != "mssql":
            self.assertEqual(
                hash_engine(auth_url),
                hash_engine(url, connect_args={"user": "user", password_key: "pass"}),
            )

            self.assertNotEqual(
                hash_engine(url, connect_args={"user": "foo"}),
                hash_engine(url, connect_args={"user": "bar"}),
            )