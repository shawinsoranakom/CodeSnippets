def test_create_with_related_manager(self):
        """
        Should be able to use update_or_create from the related manager to
        create a book. Refs #23611.
        """
        p = Publisher.objects.create(name="Acme Publishing")
        book, created = p.books.update_or_create(name="The Book of Ed & Fred")
        self.assertIs(created, True)
        self.assertEqual(p.books.count(), 1)
        book, created = p.books.update_or_create(
            name="Basics of Django", create_defaults={"name": "Advanced Django"}
        )
        self.assertIs(created, True)
        self.assertEqual(book.name, "Advanced Django")
        self.assertEqual(p.books.count(), 2)