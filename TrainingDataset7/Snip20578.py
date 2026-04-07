def test_uuid7_unsupported(self):
        if connection.vendor == "mysql":
            if connection.mysql_is_mariadb:
                msg = "UUID7 requires MariaDB version 11.7 or later."
            else:
                msg = "UUID7 is not supported on MySQL."
        elif connection.vendor == "postgresql":
            msg = "UUID7 requires PostgreSQL version 18 or later."
        elif connection.vendor == "sqlite":
            msg = "UUID7 on SQLite requires Python version 3.14 or later."
        else:
            msg = "UUID7 is not supported on this database backend."

        with self.assertRaisesMessage(NotSupportedError, msg):
            UUIDModel.objects.update(uuid=UUID7())