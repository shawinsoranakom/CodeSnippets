def test_nodb_cursor_raises_postgres_authentication_failure(self):
        """
        _nodb_cursor() re-raises authentication failure to the 'postgres' db
        when other connection to the PostgreSQL database isn't available.
        """

        def mocked_connect(self):
            raise DatabaseError()

        def mocked_all(self):
            test_connection = copy.copy(connections[DEFAULT_DB_ALIAS])
            test_connection.settings_dict = copy.deepcopy(connection.settings_dict)
            test_connection.settings_dict["NAME"] = "postgres"
            return [test_connection]

        msg = (
            "Normally Django will use a connection to the 'postgres' database "
            "to avoid running initialization queries against the production "
            "database when it's not needed (for example, when running tests). "
            "Django was unable to create a connection to the 'postgres' "
            "database and will use the first PostgreSQL database instead."
        )
        with self.assertWarnsMessage(RuntimeWarning, msg):
            mocker_connections_all = mock.patch(
                "django.utils.connection.BaseConnectionHandler.all",
                side_effect=mocked_all,
                autospec=True,
            )
            mocker_connect = mock.patch(
                "django.db.backends.base.base.BaseDatabaseWrapper.connect",
                side_effect=mocked_connect,
                autospec=True,
            )
            with mocker_connections_all, mocker_connect:
                with self.assertRaises(DatabaseError):
                    with connection._nodb_cursor():
                        pass