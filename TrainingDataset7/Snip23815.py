def setUpTestData(cls):
        cls.author = Author.objects.create(
            name="Randall Munroe",
            slug="randall-munroe",
        )