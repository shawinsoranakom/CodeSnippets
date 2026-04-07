def setUpTestData(cls):
        author = Author.objects.create(name="Boris")
        Article.objects.create(
            title="Old Article",
            slug="old_article",
            author=author,
            date_created=datetime.datetime(2001, 1, 1, 21, 22, 23),
        )
        Article.objects.create(
            title="Current Article",
            slug="current_article",
            author=author,
            date_created=datetime.datetime(2007, 9, 17, 21, 22, 23),
        )
        Article.objects.create(
            title="Future Article",
            slug="future_article",
            author=author,
            date_created=datetime.datetime(3000, 1, 1, 21, 22, 23),
        )
        cls.urlarticle = UrlArticle.objects.create(
            title="Old Article",
            slug="old_article",
            author=author,
            date_created=datetime.datetime(2001, 1, 1, 21, 22, 23),
        )
        Site(id=1, domain="testserver", name="testserver").save()