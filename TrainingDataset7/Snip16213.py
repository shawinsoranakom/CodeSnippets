def setUpTestData(cls):
        cls.superusers = {}
        cls.test_book_ids = {}
        for db in cls.databases:
            Router.target_db = db
            cls.superusers[db] = User.objects.create_superuser(
                username="admin",
                password="something",
                email="test@test.org",
            )
            b = Book(name="Test Book")
            b.save(using=db)
            cls.test_book_ids[db] = b.id