def test_mssql_sqlalchemy_engine(self):
        """Specialized tests for mssql since it uses a different way of
        passing connection arguments to the engine
        """

        url = "mssql:///?odbc_connect"
        auth_url = "mssql://foo:pass@localhost/db"

        params_foo = urllib.parse.quote_plus(
            "Server=localhost;Database=db;UID=foo;PWD=pass"
        )
        params_bar = urllib.parse.quote_plus(
            "Server=localhost;Database=db;UID=bar;PWD=pass"
        )
        params_foo_caps = urllib.parse.quote_plus(
            "SERVER=localhost;Database=db;UID=foo;PWD=pass"
        )
        params_foo_order = urllib.parse.quote_plus(
            "Database=db;Server=localhost;UID=foo;PWD=pass"
        )

        self.assertEqual(
            hash_engine(auth_url),
            hash_engine("%s=%s" % (url, params_foo)),
        )
        self.assertNotEqual(
            hash_engine("%s=%s" % (url, params_foo)),
            hash_engine("%s=%s" % (url, params_bar)),
        )

        # Note: False negative because the ordering of the keys affects
        # the hash
        self.assertNotEqual(
            hash_engine("%s=%s" % (url, params_foo)),
            hash_engine("%s=%s" % (url, params_foo_order)),
        )

        # Note: False negative because the keys are case insensitive
        self.assertNotEqual(
            hash_engine("%s=%s" % (url, params_foo)),
            hash_engine("%s=%s" % (url, params_foo_caps)),
        )

        # Note: False negative because `connect_args` doesn't affect the
        # connection string
        self.assertNotEqual(
            hash_engine(url, connect_args={"user": "foo"}),
            hash_engine(url, connect_args={"user": "bar"}),
        )