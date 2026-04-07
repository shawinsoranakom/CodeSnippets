def test_serialize_db_to_string_base_manager_with_prefetch_related(self):
        sclass = SchoolClass.objects.create(
            year=2000, last_updated=datetime.datetime.now()
        )
        bus = SchoolBus.objects.create(number=1)
        bus.schoolclasses.add(sclass)
        with mock.patch("django.db.migrations.loader.MigrationLoader") as loader:
            # serialize_db_to_string() serializes only migrated apps, so mark
            # the backends app as migrated.
            loader_instance = loader.return_value
            loader_instance.migrated_apps = {"backends"}
            data = connection.creation.serialize_db_to_string()
        self.assertIn('"model": "backends.schoolbus"', data)
        self.assertIn('"model": "backends.schoolclass"', data)
        self.assertIn(f'"schoolclasses": [{sclass.pk}]', data)