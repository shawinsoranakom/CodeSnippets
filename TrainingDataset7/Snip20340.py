def setUpTestData(cls):
        cls.author1 = Author.objects.create(alias="a", name="Jones 1")
        cls.author2 = Author.objects.create(alias="A", name="Jones 2")