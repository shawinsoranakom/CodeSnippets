def test_m2m_forward_operations(self):
        "M2M forward manipulations are all constrained to a single DB"
        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        mark = Person.objects.using("other").create(name="Mark Pilgrim")

        # Save the author relations
        dive.authors.set([mark])

        # Add a second author
        john = Person.objects.using("other").create(name="John Smith")
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="John Smith")
                .values_list("title", flat=True)
            ),
            [],
        )

        dive.authors.add(john)
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            ["Dive into Python"],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="John Smith")
                .values_list("title", flat=True)
            ),
            ["Dive into Python"],
        )

        # Remove the second author
        dive.authors.remove(john)
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            ["Dive into Python"],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="John Smith")
                .values_list("title", flat=True)
            ),
            [],
        )

        # Clear all authors
        dive.authors.clear()
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="John Smith")
                .values_list("title", flat=True)
            ),
            [],
        )

        # Create an author through the m2m interface
        dive.authors.create(name="Jane Brown")
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Mark Pilgrim")
                .values_list("title", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Book.objects.using("other")
                .filter(authors__name="Jane Brown")
                .values_list("title", flat=True)
            ),
            ["Dive into Python"],
        )