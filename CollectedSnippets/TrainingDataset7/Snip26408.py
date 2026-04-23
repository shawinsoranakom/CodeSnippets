def test_fetch_mode_copied_forward_fetching_many(self):
        Article.objects.create(
            headline="This is another test",
            pub_date=datetime.date(2005, 7, 27),
            reporter=self.r2,
        )
        a1, a2 = Article.objects.fetch_mode(FETCH_PEERS)
        self.assertEqual(a1._state.fetch_mode, FETCH_PEERS)
        self.assertEqual(
            a1.reporter._state.fetch_mode,
            FETCH_PEERS,
        )