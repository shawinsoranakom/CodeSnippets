def test_fetch_mode_copied_reverse_fetching_many(self):
        publications = list(Publication.objects.fetch_mode(FETCH_PEERS))
        p = publications[0]
        self.assertEqual(p._state.fetch_mode, FETCH_PEERS)
        articles = list(p.article_set.all())
        a = articles[0]
        self.assertEqual(
            a._state.fetch_mode,
            FETCH_PEERS,
        )