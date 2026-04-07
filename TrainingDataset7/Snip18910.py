def test_create_method_propagates_fetch_mode(self):
        article = Article.objects.fetch_mode(models.FETCH_PEERS).create(
            headline="Article 10",
            pub_date=datetime(2005, 7, 31, 12, 30, 45),
        )
        self.assertEqual(article._state.fetch_mode, models.FETCH_PEERS)