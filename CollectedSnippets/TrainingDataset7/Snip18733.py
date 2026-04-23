def test_memory_db_test_name(self):
        """A named in-memory db should be allowed where supported."""
        from django.db.backends.sqlite3.base import DatabaseWrapper

        settings_dict = {
            "TEST": {
                "NAME": "file:memorydb_test?mode=memory&cache=shared",
            }
        }
        creation = DatabaseWrapper(settings_dict).creation
        self.assertEqual(
            creation._get_test_db_name(),
            creation.connection.settings_dict["TEST"]["NAME"],
        )