def test_password_with_at_sign(self):
        from django.db.backends.oracle.base import Database

        old_password = connection.settings_dict["PASSWORD"]
        connection.settings_dict["PASSWORD"] = "p@ssword"
        try:
            self.assertIn(
                '/"p@ssword"@',
                connection.client.connect_string(connection.settings_dict),
            )
            with self.assertRaises(Database.DatabaseError) as context:
                connection.connect()
            # Database exception: "ORA-01017: invalid username/password" is
            # expected.
            self.assertIn("ORA-01017", context.exception.args[0].message)
        finally:
            connection.settings_dict["PASSWORD"] = old_password