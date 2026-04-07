def test_fetch_mode_copied_forward_fetching_one(self):
        a = Article.objects.fetch_mode(FETCH_PEERS).get(pk=self.a1.pk)
        self.assertEqual(a._state.fetch_mode, FETCH_PEERS)
        p = a.publications.earliest("pk")
        self.assertEqual(
            p._state.fetch_mode,
            FETCH_PEERS,
        )