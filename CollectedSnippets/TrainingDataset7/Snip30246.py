def test_detect_is_fetched(self):
        """
        Nested prefetch_related() shouldn't trigger duplicate queries for the
        same lookup.
        """
        with self.assertNumQueries(3):
            books = Book.objects.filter(title__in=["book1", "book2"]).prefetch_related(
                Prefetch(
                    "first_time_authors",
                    Author.objects.prefetch_related(
                        Prefetch(
                            "addresses",
                            AuthorAddress.objects.filter(address="Happy place"),
                        )
                    ),
                ),
            )
            book1, book2 = list(books)

        with self.assertNumQueries(0):
            self.assertSequenceEqual(
                book1.first_time_authors.all(), [self.author11, self.author12]
            )
            self.assertSequenceEqual(book2.first_time_authors.all(), [self.author21])

            self.assertSequenceEqual(
                book1.first_time_authors.all()[0].addresses.all(),
                [self.author1_address1],
            )
            self.assertSequenceEqual(
                book1.first_time_authors.all()[1].addresses.all(), []
            )
            self.assertSequenceEqual(
                book2.first_time_authors.all()[0].addresses.all(),
                [self.author2_address1],
            )

        self.assertEqual(
            list(book1.first_time_authors.all()),
            list(book1.first_time_authors.all().all()),
        )
        self.assertEqual(
            list(book2.first_time_authors.all()),
            list(book2.first_time_authors.all().all()),
        )
        self.assertEqual(
            list(book1.first_time_authors.all()[0].addresses.all()),
            list(book1.first_time_authors.all()[0].addresses.all().all()),
        )
        self.assertEqual(
            list(book1.first_time_authors.all()[1].addresses.all()),
            list(book1.first_time_authors.all()[1].addresses.all().all()),
        )
        self.assertEqual(
            list(book2.first_time_authors.all()[0].addresses.all()),
            list(book2.first_time_authors.all()[0].addresses.all().all()),
        )