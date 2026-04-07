def test_using_is_honored_custom_qs(self):
        B = Book.objects.using("other")
        A = Author.objects.using("other")
        book1 = B.create(title="Poems")
        book2 = B.create(title="Sense and Sensibility")

        A.create(name="Charlotte Bronte", first_book=book1)
        A.create(name="Jane Austen", first_book=book2)

        # Implicit hinting
        with self.assertNumQueries(2, using="other"):
            prefetch = Prefetch("first_time_authors", queryset=Author.objects.all())
            books = "".join(
                "%s (%s)\n"
                % (b.title, ", ".join(a.name for a in b.first_time_authors.all()))
                for b in B.prefetch_related(prefetch)
            )
        self.assertEqual(
            books,
            "Poems (Charlotte Bronte)\nSense and Sensibility (Jane Austen)\n",
        )
        # Explicit using on the same db.
        with self.assertNumQueries(2, using="other"):
            prefetch = Prefetch(
                "first_time_authors", queryset=Author.objects.using("other")
            )
            books = "".join(
                "%s (%s)\n"
                % (b.title, ", ".join(a.name for a in b.first_time_authors.all()))
                for b in B.prefetch_related(prefetch)
            )
        self.assertEqual(
            books,
            "Poems (Charlotte Bronte)\nSense and Sensibility (Jane Austen)\n",
        )

        # Explicit using on a different db.
        with (
            self.assertNumQueries(1, using="default"),
            self.assertNumQueries(1, using="other"),
        ):
            prefetch = Prefetch(
                "first_time_authors", queryset=Author.objects.using("default")
            )
            books = "".join(
                "%s (%s)\n"
                % (b.title, ", ".join(a.name for a in b.first_time_authors.all()))
                for b in B.prefetch_related(prefetch)
            )
        self.assertEqual(books, "Poems ()\n" "Sense and Sensibility ()\n")