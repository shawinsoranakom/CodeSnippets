def test_no_database(self):
        """
        Ensure runserver.check_migrations doesn't choke on empty DATABASES.
        """
        tested_connections = ConnectionHandler({})
        with mock.patch(
            "django.core.management.base.connections", new=tested_connections
        ):
            self.cmd.check_migrations()