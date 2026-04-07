def test_object_is_not_written_to_database_until_save_was_called(self):
        a = Article(
            id=None,
            headline="Parrot programs in Python",
            pub_date=datetime(2005, 7, 28),
        )
        self.assertIsNone(a.id)
        self.assertEqual(Article.objects.count(), 0)

        # Save it into the database. You have to call save() explicitly.
        a.save()
        self.assertIsNotNone(a.id)
        self.assertEqual(Article.objects.count(), 1)