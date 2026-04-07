def test_m2m_separation(self):
        "M2M fields are constrained to a single database"
        # Create a book and author on the default database
        pro = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        marty = Person.objects.create(name="Marty Alchin")

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )

        mark = Person.objects.using("other").create(name="Mark Pilgrim")

        # Save the author relations
        pro.authors.set([marty])
        dive.authors.set([mark])

        # Inspect the m2m tables directly.
        # There should be 1 entry in each database
        self.assertEqual(Book.authors.through.objects.using("default").count(), 1)
        self.assertEqual(Book.authors.through.objects.using("other").count(), 1)

        # Queries work across m2m joins
        self.assertEqual(
            list(
                Book.objects.using("default")
                .filter(authors__name="Marty Alchin")
                .values_list("title", flat=True)
            ),
            ["Pro Django"],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Marty Alchin")
                .values_list("title", flat=True)
            ),
            [],
        )

        self.assertEqual(
            list(
                Book.objects.using("default")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            ["Dive into Python"],
        )

        # Reget the objects to clear caches
        dive = Book.objects.using("other").get(title="Dive into Python")
        mark = Person.objects.using("other").get(name="Mark Pilgrim")

        # Retrieve related object by descriptor. Related objects should be
        # database-bound.
        self.assertEqual(
            list(dive.authors.values_list("name", flat=True)), ["Mark Pilgrim"]
        )

        self.assertEqual(
            list(mark.book_set.values_list("title", flat=True)),
            ["Dive into Python"],
        )