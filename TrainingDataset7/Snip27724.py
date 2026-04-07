def test_database_on_delete_serializer_value(self):
        db_level_on_delete_options = [
            models.DB_CASCADE,
            models.DB_SET_DEFAULT,
            models.DB_SET_NULL,
        ]
        for option in db_level_on_delete_options:
            self.assertSerializedEqual(option)
            self.assertSerializedResultEqual(
                MigrationWriter.serialize(option),
                (
                    f"('django.db.models.deletion.{option.__name__}', "
                    "{'import django.db.models.deletion'})",
                    set(),
                ),
            )