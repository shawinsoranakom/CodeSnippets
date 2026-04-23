def test_create_with_many(self):
        """
        Should be able to use update_or_create from the m2m related manager to
        create a book. Refs #23611.
        """
        p = Publisher.objects.create(name="Acme Publishing")
        author = Author.objects.create(name="Ted")
        book, created = author.books.update_or_create(
            name="The Book of Ed & Fred", publisher=p
        )
        self.assertIs(created, True)
        self.assertEqual(author.books.count(), 1)
        book, created = author.books.update_or_create(
            name="Basics of Django",
            publisher=p,
            create_defaults={"name": "Advanced Django"},
        )
        self.assertIs(created, True)
        self.assertEqual(book.name, "Advanced Django")
        self.assertEqual(author.books.count(), 2)