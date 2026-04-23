def setUpTestData(cls):
        # Create an Article.
        cls.a = Article(
            id=None,
            headline="Swallow programs in Python",
            pub_date=datetime(2005, 7, 28),
        )
        # Save it into the database. You have to call save() explicitly.
        cls.a.save()