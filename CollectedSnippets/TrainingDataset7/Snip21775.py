def test_both_default(self):
        create_sql = connection.features.insert_test_table_with_defaults
        with connection.cursor() as cursor:
            cursor.execute(create_sql.format(DBDefaults._meta.db_table))
        obj1 = DBDefaults.objects.get()
        self.assertEqual(obj1.both, 2)

        obj2 = DBDefaults.objects.create()
        self.assertEqual(obj2.both, 1)