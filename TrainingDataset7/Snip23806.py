def setUpTestData(cls):
        cls.author = Author.objects.create(
            pk=1,  # Required for OneAuthorUpdate.
            name="Randall Munroe",
            slug="randall-munroe",
        )