def test_fetch_mode_fetch_peers_forward(self):
        Article.objects.create(
            headline="This is another test",
            pub_date=datetime.date(2005, 7, 27),
            reporter=self.r2,
        )
        a1, a2 = Article.objects.fetch_mode(FETCH_PEERS)
        with self.assertNumQueries(1):
            a1.reporter
        with self.assertNumQueries(0):
            a2.reporter