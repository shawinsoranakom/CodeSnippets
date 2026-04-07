def test_fetch_mode_copied_forward_fetching_one(self):
        a1 = Article.objects.fetch_mode(FETCH_PEERS).get()
        self.assertEqual(a1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            a1.reporter._state.fetch_mode,
            FETCH_PEERS,
        )