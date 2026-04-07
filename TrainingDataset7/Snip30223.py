def test_m2m_to_inheriting_model(self):
        qs = AuthorWithAge.objects.prefetch_related("books_with_year")
        with self.assertNumQueries(2):
            lst = [
                [str(book) for book in author.books_with_year.all()] for author in qs
            ]
        qs = AuthorWithAge.objects.all()
        lst2 = [[str(book) for book in author.books_with_year.all()] for author in qs]
        self.assertEqual(lst, lst2)

        qs = BookWithYear.objects.prefetch_related("aged_authors")
        with self.assertNumQueries(2):
            lst = [[str(author) for author in book.aged_authors.all()] for book in qs]
        qs = BookWithYear.objects.all()
        lst2 = [[str(author) for author in book.aged_authors.all()] for book in qs]
        self.assertEqual(lst, lst2)