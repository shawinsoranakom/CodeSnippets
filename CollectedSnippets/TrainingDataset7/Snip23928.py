def test_update_with_many(self):
        """
        Should be able to use update_or_create from the m2m related manager to
        update a book. Refs #23611.
        """
        p = Publisher.objects.create(name="Acme Publishing")
        author = Author.objects.create(name="Ted")
        book = Book.objects.create(name="The Book of Ed & Fred", publisher=p)
        book.authors.add(author)
        self.assertEqual(author.books.count(), 1)
        name = "The Book of Django"
        book, created = author.books.update_or_create(
            defaults={"name": name}, id=book.id
        )
        self.assertFalse(created)
        self.assertEqual(book.name, name)
        # create_defaults should be ignored.
        book, created = author.books.update_or_create(
            create_defaults={"name": "Basics of Django"},
            defaults={"name": name},
            id=book.id,
        )
        self.assertIs(created, False)
        self.assertEqual(book.name, name)
        self.assertEqual(author.books.count(), 1)