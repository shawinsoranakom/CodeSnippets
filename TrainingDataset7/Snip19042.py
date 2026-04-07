def test_db_default_primary_key(self):
        (obj,) = DbDefaultPrimaryKey.objects.bulk_create([DbDefaultPrimaryKey()])
        self.assertIsInstance(obj.id, datetime)