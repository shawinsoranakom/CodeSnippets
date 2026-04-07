def test_foreign_key_separation(self):
        "FK fields are constrained to a single database"
        # Create a book and author on the default database
        pro = Book.objects.create(
            title="Pro Django", published=datetime.date(2008, 12, 16)
        )

        george = Person.objects.create(name="George Vilches")

        # Create a book and author on the other database
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        chris = Person.objects.using("other").create(name="Chris Mills")

        # Save the author's favorite books
        pro.editor = george
        pro.save()

        dive.editor = chris
        dive.save()

        pro = Book.objects.using("default").get(title="Pro Django")
        self.assertEqual(pro.editor.name, "George Vilches")

        dive = Book.objects.using("other").get(title="Dive into Python")
        self.assertEqual(dive.editor.name, "Chris Mills")

        # Queries work across foreign key joins
        self.assertEqual(
            list(
                Person.objects.using("default")
                .filter(edited__title="Pro Django")
                .values_list("name", flat=True)
            ),
            ["George Vilches"],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Pro Django")
                .values_list("name", flat=True)
            ),
            [],
        )

        self.assertEqual(
            list(
                Person.objects.using("default")
                .filter(edited__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            ["Chris Mills"],
        )

        # Reget the objects to clear caches
        chris = Person.objects.using("other").get(name="Chris Mills")
        dive = Book.objects.using("other").get(title="Dive into Python")

        # Retrieve related object by descriptor. Related objects should be
        # database-bound.
        self.assertEqual(
            list(chris.edited.values_list("title", flat=True)), ["Dive into Python"]
        )