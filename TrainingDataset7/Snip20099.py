def setUpTestData(cls):
        cls.a1 = Author.objects.create(first_name="John", last_name="Smith")
        cls.a2 = Author.objects.create(first_name="Peter", last_name="Jones")
        cls.authors = [cls.a1, cls.a2]

        cls.article = Article.objects.create(
            headline="Django lets you build web apps easily", primary_author=cls.a1
        )
        cls.article.authors.set(cls.authors)