def test_invalid_transaction_mode(self):
        msg = (
            "settings.DATABASES['default']['OPTIONS']['transaction_mode'] is "
            "improperly configured to 'invalid'. Use one of 'DEFERRED', 'EXCLUSIVE', "
            "'IMMEDIATE', or None."
        )
        with self.change_transaction_mode("invalid") as new_connection:
            with self.assertRaisesMessage(ImproperlyConfigured, msg):
                new_connection.ensure_connection()