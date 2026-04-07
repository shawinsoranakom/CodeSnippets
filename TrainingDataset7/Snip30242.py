def test_bug(self):
        list(Author2.objects.prefetch_related("first_book", "favorite_books"))