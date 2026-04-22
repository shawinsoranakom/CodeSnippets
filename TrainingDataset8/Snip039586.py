def test_sqlite_sqlalchemy_engine(self):
        """Separate tests for sqlite since it uses a file based
        and in memory database and has no auth
        """

        mem = "sqlite://"
        foo = "sqlite:///foo.db"

        self.assertEqual(hash_engine(mem), hash_engine(mem))
        self.assertEqual(hash_engine(foo), hash_engine(foo))
        self.assertNotEqual(hash_engine(foo), hash_engine("sqlite:///bar.db"))
        self.assertNotEqual(hash_engine(foo), hash_engine(mem))

        # Need to use absolute paths otherwise one path resolves
        # relatively and the other absolute
        self.assertEqual(
            hash_engine("sqlite:////foo.db", connect_args={"uri": True}),
            hash_engine("sqlite:////foo.db?uri=true"),
        )

        self.assertNotEqual(
            hash_engine(foo, connect_args={"uri": True}),
            hash_engine(foo, connect_args={"uri": False}),
        )

        self.assertNotEqual(
            hash_engine(foo, creator=lambda: False),
            hash_engine(foo, creator=lambda: True),
        )