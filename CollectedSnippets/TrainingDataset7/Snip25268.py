def test_unmanaged_through_model(self):
        tables = connection.introspection.django_table_names()
        self.assertNotIn(ArticleReporter._meta.db_table, tables)