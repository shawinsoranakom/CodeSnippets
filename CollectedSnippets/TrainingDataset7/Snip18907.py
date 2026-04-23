def test_microsecond_precision(self):
        a9 = Article(
            headline="Article 9",
            pub_date=datetime(2005, 7, 31, 12, 30, 45, 180),
        )
        a9.save()
        self.assertEqual(
            Article.objects.get(pk=a9.pk).pub_date,
            datetime(2005, 7, 31, 12, 30, 45, 180),
        )