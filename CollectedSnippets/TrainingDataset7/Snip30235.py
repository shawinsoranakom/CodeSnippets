def test_using_is_honored_m2m(self):
        B = Book.objects.using("other")
        A = Author.objects.using("other")
        book1 = B.create(title="Poems")
        book2 = B.create(title="Jane Eyre")
        book3 = B.create(title="Wuthering Heights")
        book4 = B.create(title="Sense and Sensibility")

        author1 = A.create(name="Charlotte", first_book=book1)
        author2 = A.create(name="Anne", first_book=book1)
        author3 = A.create(name="Emily", first_book=book1)
        author4 = A.create(name="Jane", first_book=book4)

        book1.authors.add(author1, author2, author3)
        book2.authors.add(author1)
        book3.authors.add(author3)
        book4.authors.add(author4)

        # Forward
        qs1 = B.prefetch_related("authors")
        with self.assertNumQueries(2, using="other"):
            books = "".join(
                "%s (%s)\n"
                % (book.title, ", ".join(a.name for a in book.authors.all()))
                for book in qs1
            )
        self.assertEqual(
            books,
            "Poems (Charlotte, Anne, Emily)\n"
            "Jane Eyre (Charlotte)\n"
            "Wuthering Heights (Emily)\n"
            "Sense and Sensibility (Jane)\n",
        )

        # Reverse
        qs2 = A.prefetch_related("books")
        with self.assertNumQueries(2, using="other"):
            authors = "".join(
                "%s: %s\n"
                % (author.name, ", ".join(b.title for b in author.books.all()))
                for author in qs2
            )
        self.assertEqual(
            authors,
            "Charlotte: Poems, Jane Eyre\n"
            "Anne: Poems\n"
            "Emily: Poems, Wuthering Heights\n"
            "Jane: Sense and Sensibility\n",
        )