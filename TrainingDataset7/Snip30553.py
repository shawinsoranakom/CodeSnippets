def test_subquery_annotation(self):
        query = Query(None)
        query.add_annotation(Exists(Item.objects.all()), "_check")
        result = query.get_compiler(using=DEFAULT_DB_ALIAS).execute_sql(SINGLE)
        self.assertEqual(result[0], 0)