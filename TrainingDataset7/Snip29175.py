def test_foreign_key_managers(self):
        """
        FK reverse relations are represented by managers, and can be controlled
        like managers.
        """
        marty = Person.objects.using("other").create(pk=1, name="Marty Alchin")
        Book.objects.using("other").create(
            pk=1,
            title="Pro Django",
            published=datetime.date(2008, 12, 16),
            editor=marty,
        )
        self.assertEqual(marty.edited.db, "other")
        self.assertEqual(marty.edited.db_manager("default").db, "default")
        self.assertEqual(marty.edited.db_manager("default").all().db, "default")