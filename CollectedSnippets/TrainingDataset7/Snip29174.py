def test_m2m_managers(self):
        """
        M2M relations are represented by managers, and can be controlled like
        managers
        """
        pro = Book.objects.using("other").create(
            pk=1, title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        marty = Person.objects.using("other").create(pk=1, name="Marty Alchin")

        self.assertEqual(pro.authors.db, "other")
        self.assertEqual(pro.authors.db_manager("default").db, "default")
        self.assertEqual(pro.authors.db_manager("default").all().db, "default")

        self.assertEqual(marty.book_set.db, "other")
        self.assertEqual(marty.book_set.db_manager("default").db, "default")
        self.assertEqual(marty.book_set.db_manager("default").all().db, "default")