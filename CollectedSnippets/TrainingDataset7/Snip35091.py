def test_transaction_support(self):
        # Assert connections mocking is appropriately applied by preventing
        # any attempts at calling create_test_db on the global connection
        # objects.
        for connection in db.connections.all():
            create_test_db = mock.patch.object(
                connection.creation,
                "create_test_db",
                side_effect=AssertionError(
                    "Global connection object shouldn't be manipulated."
                ),
            )
            create_test_db.start()
            self.addCleanup(create_test_db.stop)
        for option_key, option_value in (
            ("NAME", ":memory:"),
            ("TEST", {"NAME": ":memory:"}),
        ):
            tested_connections = db.ConnectionHandler(
                {
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        option_key: option_value,
                    },
                    "other": {
                        "ENGINE": "django.db.backends.sqlite3",
                        option_key: option_value,
                    },
                }
            )
            with mock.patch("django.test.utils.connections", new=tested_connections):
                other = tested_connections["other"]
                try:
                    new_test_connections = DiscoverRunner(verbosity=0).setup_databases()
                    msg = (
                        f"DATABASES setting '{option_key}' option set to sqlite3's "
                        "':memory:' value shouldn't interfere with transaction support "
                        "detection."
                    )
                    # Transaction support is properly initialized for the
                    # 'other' DB.
                    self.assertTrue(other.features.supports_transactions, msg)
                    # And all the DBs report that they support transactions.
                    self.assertTrue(connections_support_transactions(), msg)
                finally:
                    for test_connection, _, _ in new_test_connections:
                        test_connection._close()