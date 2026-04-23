def test_pk(self):
        self.assertEqual(Relation._meta.db_returning_fields, [Relation._meta.pk])