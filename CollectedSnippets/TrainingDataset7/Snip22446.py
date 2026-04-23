def test_foreign_key_related_query_name(self):
        a1 = Article.objects.create(pub_date=datetime.date.today())
        ArticleTag.objects.create(article=a1, name="foo")
        self.assertEqual(Article.objects.filter(tag__name="foo").count(), 1)
        self.assertEqual(Article.objects.filter(tag__name="bar").count(), 0)
        msg = (
            "Cannot resolve keyword 'tags' into field. Choices are: "
            "active_translation, active_translation_q, articletranslation, "
            "id, idea_things, newsarticle, pub_date, tag"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(tags__name="foo")