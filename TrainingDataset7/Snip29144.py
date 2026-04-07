def test_m2m_deletion(self):
        """
        Cascaded deletions of m2m relations issue queries on the right database
        """
        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        mark = Person.objects.using("other").create(name="Mark Pilgrim")
        dive.authors.set([mark])

        # Check the initial state
        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Book.authors.through.objects.using("default").count(), 0)

        self.assertEqual(Person.objects.using("other").count(), 1)
        self.assertEqual(Book.objects.using("other").count(), 1)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 1)

        # Delete the object on the other database
        dive.delete(using="other")

        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Book.authors.through.objects.using("default").count(), 0)

        # The person still exists ...
        self.assertEqual(Person.objects.using("other").count(), 1)
        # ... but the book has been deleted
        self.assertEqual(Book.objects.using("other").count(), 0)
        # ... and the relationship object has also been deleted.
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)

        # Now try deletion in the reverse direction. Set up the relation again
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        dive.authors.set([mark])

        # Check the initial state
        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Book.authors.through.objects.using("default").count(), 0)

        self.assertEqual(Person.objects.using("other").count(), 1)
        self.assertEqual(Book.objects.using("other").count(), 1)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 1)

        # Delete the object on the other database
        mark.delete(using="other")

        self.assertEqual(Person.objects.using("default").count(), 0)
        self.assertEqual(Book.objects.using("default").count(), 0)
        self.assertEqual(Book.authors.through.objects.using("default").count(), 0)

        # The person has been deleted ...
        self.assertEqual(Person.objects.using("other").count(), 0)
        # ... but the book still exists
        self.assertEqual(Book.objects.using("other").count(), 1)
        # ... and the relationship object has been deleted.
        self.assertEqual(Book.authors.through.objects.using("other").count(), 0)