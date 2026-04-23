def sql_table_creation_suffix(self):
        test_settings = self.connection.settings_dict["TEST"]
        if test_settings.get("COLLATION") is not None:
            raise ImproperlyConfigured(
                "PostgreSQL does not support collation setting at database "
                "creation time."
            )
        return self._get_database_create_suffix(
            encoding=test_settings["CHARSET"],
            template=test_settings.get("TEMPLATE"),
        )