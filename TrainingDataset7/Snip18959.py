def test_refresh_overwrites_queryset_using(self):
        a = Article.objects.create(pub_date=datetime.now())

        from_queryset = Article.objects.using("nonexistent")
        with self.assertRaises(ConnectionDoesNotExist):
            a.refresh_from_db(from_queryset=from_queryset)
        a.refresh_from_db(using="default", from_queryset=from_queryset)