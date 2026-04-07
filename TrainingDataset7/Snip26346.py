def test_fetch_mode_copied_forward_fetching_many(self):
        articles = list(Article.objects.fetch_mode(FETCH_PEERS))
        a = articles[0]
        self.assertEqual(a._state.fetch_mode, FETCH_PEERS)
        publications = list(a.publications.all())
        p = publications[0]
        self.assertEqual(
            p._state.fetch_mode,
            FETCH_PEERS,
        )