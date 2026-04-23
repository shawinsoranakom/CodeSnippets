def test_foreignkey_forward(self):
        with self.assertNumQueries(2):
            books = [
                a.first_book for a in Author.objects.prefetch_related("first_book")
            ]

        normal_books = [a.first_book for a in Author.objects.all()]
        self.assertEqual(books, normal_books)