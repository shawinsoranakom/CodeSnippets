def test_joined_annotation(self):
        books = Book.objects.select_related("publisher").annotate(
            num_awards=F("publisher__num_awards")
        )
        for book in books:
            self.assertEqual(book.num_awards, book.publisher.num_awards)