def setUpTestData(cls):
        cls.article = Article.objects.create(
            headline="Django lets you build Web apps easily"
        )
        cls.nullable_target_article = NullableTargetArticle.objects.create(
            headline="The python is good"
        )
        NullablePublicationThrough.objects.create(
            article=cls.nullable_target_article, publication=None
        )