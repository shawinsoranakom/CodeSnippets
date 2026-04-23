def test_self_reference(self):
        # serialize_db_to_string() and deserialize_db_from_string() handles
        # self references.
        obj_1 = ObjectSelfReference.objects.create(key="X")
        obj_2 = ObjectSelfReference.objects.create(key="Y", obj=obj_1)
        obj_1.obj = obj_2
        obj_1.save()
        # Serialize objects.
        with mock.patch("django.db.migrations.loader.MigrationLoader") as loader:
            # serialize_db_to_string() serializes only migrated apps, so mark
            # the backends app as migrated.
            loader_instance = loader.return_value
            loader_instance.migrated_apps = {"backends"}
            data = connection.creation.serialize_db_to_string()
        ObjectSelfReference.objects.all().delete()
        # Deserialize objects.
        connection.creation.deserialize_db_from_string(data)
        obj_1 = ObjectSelfReference.objects.get(key="X")
        obj_2 = ObjectSelfReference.objects.get(key="Y")
        self.assertEqual(obj_1.obj, obj_2)
        self.assertEqual(obj_2.obj, obj_1)