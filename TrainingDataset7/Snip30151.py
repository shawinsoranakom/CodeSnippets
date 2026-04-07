def test_fetch_mode_raise(self):
        authors = list(Author.objects.fetch_mode(RAISE).prefetch_related("first_book"))
        authors[0].first_book