def test_db_selection(self):
        "Querysets obey the router for db suggestions"
        self.assertEqual(Book.objects.db, "other")
        self.assertEqual(Book.objects.all().db, "other")

        self.assertEqual(Book.objects.using("default").db, "default")

        self.assertEqual(Book.objects.db_manager("default").db, "default")
        self.assertEqual(Book.objects.db_manager("default").all().db, "default")