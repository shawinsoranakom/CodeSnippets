def test_inheritance(self):
        na = NewsArticle.objects.create(pub_date=datetime.date.today())
        ArticleTranslation.objects.create(
            article=na, lang="fi", title="foo", body="bar"
        )
        self.assertSequenceEqual(
            NewsArticle.objects.select_related("active_translation"), [na]
        )
        with self.assertNumQueries(1):
            self.assertEqual(
                NewsArticle.objects.select_related("active_translation")[
                    0
                ].active_translation.title,
                "foo",
            )