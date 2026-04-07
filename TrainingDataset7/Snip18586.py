def test_isolation_level_validation(self):
        new_connection = connection.copy()
        new_connection.settings_dict["OPTIONS"]["isolation_level"] = "xxx"
        msg = (
            "Invalid transaction isolation level 'xxx' specified.\n"
            "Use one of 'read committed', 'read uncommitted', "
            "'repeatable read', 'serializable', or None."
        )
        with self.assertRaisesMessage(ImproperlyConfigured, msg):
            new_connection.cursor()