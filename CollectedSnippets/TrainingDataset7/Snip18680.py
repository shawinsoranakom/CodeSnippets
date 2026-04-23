def test_connect_role(self):
        """
        The session role can be configured with DATABASES
        ["OPTIONS"]["assume_role"].
        """
        try:
            custom_role = "django_nonexistent_role"
            new_connection = no_pool_connection()
            new_connection.settings_dict["OPTIONS"]["assume_role"] = custom_role
            msg = f'role "{custom_role}" does not exist'
            with self.assertRaisesMessage(errors.InvalidParameterValue, msg):
                new_connection.connect()
        finally:
            new_connection.close()