def test_fetch_mode_copied_fetching_one(self):
        author = (
            Author.objects.fetch_mode(FETCH_PEERS)
            .prefetch_related("first_book")
            .get(pk=self.author1.pk)
        )
        self.assertEqual(author._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            author.first_book._state.fetch_mode,
            FETCH_PEERS,
        )