def setUpTestData(cls):
        # Prepare a list of objects for pagination.
        pub_date = datetime(2005, 7, 29)
        cls.articles = [
            Article.objects.create(headline=f"Article {x}", pub_date=pub_date)
            for x in range(1, 10)
        ]