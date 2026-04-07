def test_many_to_many_related_query_name(self):
        a1 = Article.objects.create(pub_date=datetime.date.today())
        i1 = ArticleIdea.objects.create(name="idea1")
        a1.ideas.add(i1)
        self.assertEqual(Article.objects.filter(idea_things__name="idea1").count(), 1)
        self.assertEqual(Article.objects.filter(idea_things__name="idea2").count(), 0)
        msg = (
            "Cannot resolve keyword 'ideas' into field. Choices are: "
            "active_translation, active_translation_q, articletranslation, "
            "id, idea_things, newsarticle, pub_date, tag"
        )
        with self.assertRaisesMessage(FieldError, msg):
            Article.objects.filter(ideas__name="idea1")