def test_using_is_honored_fkey(self):
        B = Book.objects.using("other")
        A = Author.objects.using("other")
        book1 = B.create(title="Poems")
        book2 = B.create(title="Sense and Sensibility")

        A.create(name="Charlotte Bronte", first_book=book1)
        A.create(name="Jane Austen", first_book=book2)

        # Forward
        with self.assertNumQueries(2, using="other"):
            books = ", ".join(
                a.first_book.title for a in A.prefetch_related("first_book")
            )
        self.assertEqual("Poems, Sense and Sensibility", books)

        # Reverse
        with self.assertNumQueries(2, using="other"):
            books = "".join(
                "%s (%s)\n"
                % (b.title, ", ".join(a.name for a in b.first_time_authors.all()))
                for b in B.prefetch_related("first_time_authors")
            )
        self.assertEqual(
            books,
            "Poems (Charlotte Bronte)\nSense and Sensibility (Jane Austen)\n",
        )