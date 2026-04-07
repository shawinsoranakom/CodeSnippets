def test_foreign_key_reverse_operations(self):
        "FK reverse manipulations are all constrained to a single DB"
        dive = Book.objects.using("other").create(
            title="Dive into Python", published=datetime.date(2009, 5, 4)
        )
        chris = Person.objects.using("other").create(name="Chris Mills")

        # Save the author relations
        dive.editor = chris
        dive.save()

        # Add a second book edited by chris
        html5 = Book.objects.using("other").create(
            title="Dive into HTML5", published=datetime.date(2010, 3, 15)
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into HTML5")
                .values_list("name", flat=True)
            ),
            [],
        )

        chris.edited.add(html5)
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into HTML5")
                .values_list("name", flat=True)
            ),
            ["Chris Mills"],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            ["Chris Mills"],
        )

        # Remove the second editor
        chris.edited.remove(html5)
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into HTML5")
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

        # Clear all edited books
        chris.edited.clear()
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into HTML5")
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
            [],
        )

        # Create an author through the m2m interface
        chris.edited.create(
            title="Dive into Water", published=datetime.date(2010, 3, 15)
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into HTML5")
                .values_list("name", flat=True)
            ),
            [],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into Water")
                .values_list("name", flat=True)
            ),
            ["Chris Mills"],
        )
        self.assertEqual(
            list(
                Person.objects.using("other")
                .filter(edited__title="Dive into Python")
                .values_list("name", flat=True)
            ),
            [],
        )