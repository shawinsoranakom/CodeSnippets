def test_nodb_cursor(self):
        """
        The _nodb_cursor() fallbacks to the default connection database when
        access to the 'postgres' database is not granted.
        """
        orig_connect = BaseDatabaseWrapper.connect

        def mocked_connect(self):
            if self.settings_dict["NAME"] is None:
                raise DatabaseError()
            return orig_connect(self)

        with connection._nodb_cursor() as cursor:
            self.assertIs(cursor.closed, False)
            self.assertIsNotNone(cursor.db.connection)
            self.assertIsNone(cursor.db.settings_dict["NAME"])
        self.assertIs(cursor.closed, True)
        self.assertIsNone(cursor.db.connection)

        # Now assume the 'postgres' db isn't available
        msg = (
            "Normally Django will use a connection to the 'postgres' database "
            "to avoid running initialization queries against the production "
            "database when it's not needed (for example, when running tests). "
            "Django was unable to create a connection to the 'postgres' "
            "database and will use the first PostgreSQL database instead."
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            with mock.patch(
                "django.db.backends.base.base.BaseDatabaseWrapper.connect",
                side_effect=mocked_connect,
                autospec=True,
            ):
                with mock.patch.object(
                    connection,
                    "settings_dict",
                    {**connection.settings_dict, "NAME": "postgres"},
                ):
                    with connection._nodb_cursor() as cursor:
                        self.assertIs(cursor.closed, False)
                        self.assertIsNotNone(cursor.db.connection)
        self.assertIs(cursor.closed, True)
        self.assertIsNone(cursor.db.connection)
        self.assertIsNotNone(cursor.db.settings_dict["NAME"])
        self.assertEqual(
            cursor.db.settings_dict["NAME"], connections["other"].settings_dict["NAME"]
        )
        # Cursor is yielded only for the first PostgreSQL database.
        with self.assertWarnsMessage(RuntimeWarning, msg):
            with mock.patch(
                "django.db.backends.base.base.BaseDatabaseWrapper.connect",
                side_effect=mocked_connect,
                autospec=True,
            ):
                with connection._nodb_cursor() as cursor:
                    self.assertIs(cursor.closed, False)
                    self.assertIsNotNone(cursor.db.connection)