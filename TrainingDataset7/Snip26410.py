def test_fetch_mode_copied_reverse_fetching_many(self):
        Article.objects.create(
            headline="This is another test",
            pub_date=datetime.date(2005, 7, 27),
            reporter=self.r2,
        )
        r1, r2 = Reporter.objects.fetch_mode(FETCH_PEERS)
        self.assertEqual(r1._state.fetch_mode, FETCH_PEERS)
        a1 = r1.article_set.get()
        self.assertEqual(
            a1._state.fetch_mode,
            FETCH_PEERS,
        )
        a2 = r2.article_set.get()
        self.assertEqual(
            a2._state.fetch_mode,
            FETCH_PEERS,
        )