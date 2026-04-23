def test_fetch_mode_copied_reverse_fetching_one(self):
        p1 = Publication.objects.fetch_mode(FETCH_PEERS).get(pk=self.p1.pk)
        self.assertEqual(p1._state.fetch_mode, FETCH_PEERS)
        a = p1.article_set.earliest("pk")
        self.assertEqual(
            a._state.fetch_mode,
            FETCH_PEERS,
        )