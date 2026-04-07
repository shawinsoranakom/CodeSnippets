def test_fetch_mode_copied_reverse_fetching_one(self):
        r1 = Reporter.objects.fetch_mode(FETCH_PEERS).get(pk=self.r.pk)
        self.assertEqual(r1._state.fetch_mode, FETCH_PEERS)
        article = r1.article_set.get()
        self.assertEqual(
            article._state.fetch_mode,
            FETCH_PEERS,
        )