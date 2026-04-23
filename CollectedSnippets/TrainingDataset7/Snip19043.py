def test_db_expression_primary_key(self):
        (obj,) = DbDefaultPrimaryKey.objects.bulk_create(
            [DbDefaultPrimaryKey(id=Now())]
        )
        self.assertIsInstance(obj.id, datetime)