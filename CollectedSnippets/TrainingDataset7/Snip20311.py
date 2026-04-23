def test_21432(self):
        now = timezone.localtime(timezone.now().replace(microsecond=0))
        Article.objects.create(title="First one", pub_date=now)
        qs = Article.objects.datetimes("pub_date", "second")
        self.assertEqual(qs[0], now)