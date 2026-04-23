def test_fetch_mode_copied_fetching_many(self):
        authors = list(
            Author.objects.fetch_mode(FETCH_PEERS).prefetch_related("first_book")
        )
        self.assertEqual(authors[0]._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            authors[0].first_book._state.fetch_mode,
            FETCH_PEERS,
        )