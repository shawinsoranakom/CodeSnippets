def setUpTestData(cls):
        Article.objects.create(name="Article 1", created=datetime.datetime.now())
        Article.objects.create(name="Article 2", created=datetime.datetime.now())