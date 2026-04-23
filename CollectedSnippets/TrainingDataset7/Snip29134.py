def test_db_selection(self):
        "Querysets will use the default database by default"
        self.assertEqual(Book.objects.db, DEFAULT_DB_ALIAS)
        self.assertEqual(Book.objects.all().db, DEFAULT_DB_ALIAS)

        self.assertEqual(Book.objects.using("other").db, "other")

        self.assertEqual(Book.objects.db_manager("other").db, "other")
        self.assertEqual(Book.objects.db_manager("other").all().db, "other")