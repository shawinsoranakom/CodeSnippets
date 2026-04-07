def test_null_ordering_added(self):
        query = Tag.objects.values_list("parent_id", flat=True).order_by().query
        query.group_by = ["parent_id"]
        sql = query.get_compiler(DEFAULT_DB_ALIAS).as_sql()[0]
        fragment = "ORDER BY "
        pos = sql.find(fragment)
        self.assertEqual(sql.find(fragment, pos + 1), -1)
        self.assertEqual(sql.find("NULL", pos + len(fragment)), pos + len(fragment))