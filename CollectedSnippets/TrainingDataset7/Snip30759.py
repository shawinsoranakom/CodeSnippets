def setUpTestData(cls):
        some_date = datetime.datetime(2014, 5, 16, 12, 1)
        cls.articles = [
            Article.objects.create(name=f"Article {i}", created=some_date)
            for i in range(1, 8)
        ]