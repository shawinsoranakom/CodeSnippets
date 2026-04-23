def test_nonexistent_alias(self):
        msg = "The connection 'nonexistent' doesn't exist."
        conns = ConnectionHandler(
            {
                DEFAULT_DB_ALIAS: {"ENGINE": "django.db.backends.dummy"},
            }
        )
        with self.assertRaisesMessage(ConnectionDoesNotExist, msg):
            conns["nonexistent"]