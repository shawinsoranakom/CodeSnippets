def test_serialize_db_to_string_base_manager(self):
        SchoolClass.objects.create(year=1000, last_updated=datetime.datetime.now())
        with mock.patch("django.db.migrations.loader.MigrationLoader") as loader:
            # serialize_db_to_string() serializes only migrated apps, so mark
            # the backends app as migrated.
            loader_instance = loader.return_value
            loader_instance.migrated_apps = {"backends"}
            data = connection.creation.serialize_db_to_string()
        self.assertIn('"model": "backends.schoolclass"', data)
        self.assertIn('"year": 1000', data)