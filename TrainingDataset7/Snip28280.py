def setUpTestData(cls):
        cls.c1 = Category.objects.create(
            name="Entertainment", slug="entertainment", url="entertainment"
        )
        cls.c2 = Category.objects.create(name="A test", slug="test", url="test")
        cls.c3 = Category.objects.create(name="Third", slug="third-test", url="third")