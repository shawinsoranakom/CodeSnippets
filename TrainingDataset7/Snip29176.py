def test_generic_key_managers(self):
        """
        Generic key relations are represented by managers, and can be
        controlled like managers.
        """
        pro = Book.objects.using("other").create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        Review.objects.using("other").create(
            source="Python Monthly", content_object=pro
        )

        self.assertEqual(pro.reviews.db, "other")
        self.assertEqual(pro.reviews.db_manager("default").db, "default")
        self.assertEqual(pro.reviews.db_manager("default").all().db, "default")