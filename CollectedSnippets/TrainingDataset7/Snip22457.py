def test_extra_join_filter_q(self):
        a = Article.objects.create(pub_date=datetime.datetime.today())
        ArticleTranslation.objects.create(
            article=a, lang="fi", title="title", body="body"
        )
        qs = Article.objects.all()
        with self.assertNumQueries(2):
            self.assertEqual(qs[0].active_translation_q.title, "title")
        qs = qs.select_related("active_translation_q")
        with self.assertNumQueries(1):
            self.assertEqual(qs[0].active_translation_q.title, "title")