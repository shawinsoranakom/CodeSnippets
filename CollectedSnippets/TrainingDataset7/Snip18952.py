def test_refresh_no_fields(self):
        a = Article.objects.create(pub_date=datetime.now())
        with self.assertNumQueries(0):
            a.refresh_from_db(fields=[])