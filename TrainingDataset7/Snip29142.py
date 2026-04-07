def test_m2m_reverse_operations(self):
        "M2M reverse manipulations are all constrained to a single DB"
        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        mark = Person.objects.using("other").create(name="Mark Pilgrim")

        # Save the author relations
        dive.authors.set([mark])

        # Create a second book on the other database
        grease = Book.objects.using("other").create(
            title="Greasemonkey Hacks", published=datetime.date(2005, 11, 1)
        )

        # Add a books to the m2m
        mark.book_set.add(grease)
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            ["Mark Pilgrim"],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Greasemonkey Hacks")
                .values_list("name", flat=True)
            ),
            ["Mark Pilgrim"],
        )

        # Remove a book from the m2m
        mark.book_set.remove(grease)
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            ["Mark Pilgrim"],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Greasemonkey Hacks")
                .values_list("name", flat=True)
            ),
            [],
        )

        # Clear the books associated with mark
        mark.book_set.clear()
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Greasemonkey Hacks")
                .values_list("name", flat=True)
            ),
            [],
        )

        # Create a book through the m2m interface
        mark.book_set.create(
            title="Dive into HTML5", published=datetime.date(2020, 1, 1)
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(book__title="Dive into HTML5")
                .values_list("name", flat=True)
            ),
            ["Mark Pilgrim"],
        )