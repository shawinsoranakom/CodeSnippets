def test_debug_sql(self):
        list(Reporter.objects.filter(first_name="test"))
        sql = connection.queries[-1]["sql"].lower()
        self.assertIn("select", sql)
        self.assertIn(Reporter._meta.db_table, sql)