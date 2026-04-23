def test_order_by_self_referential_fk(self):
        self.a1.author = Author.objects.create(editor=self.author_1)
        self.a1.save()
        self.a2.author = Author.objects.create(editor=self.author_2)
        self.a2.save()
        self.assertQuerySetEqual(
            Article.objects.filter(author__isnull=False).order_by("author__editor"),
            ["Article 2", "Article 1"],
            attrgetter("headline"),
        )
        self.assertQuerySetEqual(
            Article.objects.filter(author__isnull=False).order_by("author__editor_id"),
            ["Article 1", "Article 2"],
            attrgetter("headline"),
        )