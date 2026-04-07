def test_detect_is_fetched_with_to_attr(self):
        with self.assertNumQueries(3):
            books = Book.objects.filter(title__in=["book1", "book2"]).prefetch_related(
                Prefetch(
                    "first_time_authors",
                    Author.objects.prefetch_related(
                        Prefetch(
                            "addresses",
                            AuthorAddress.objects.filter(address="Happy place"),
                            to_attr="happy_place",
                        )
                    ),
                    to_attr="first_authors",
                ),
            )
            book1, book2 = list(books)

        with self.assertNumQueries(0):
            self.assertEqual(book1.first_authors, [self.author11, self.author12])
            self.assertEqual(book2.first_authors, [self.author21])

            self.assertEqual(
                book1.first_authors[0].happy_place, [self.author1_address1]
            )
            self.assertEqual(book1.first_authors[1].happy_place, [])
            self.assertEqual(
                book2.first_authors[0].happy_place, [self.author2_address1]
            )