def setUpTestData(cls):
        SimpleCategory.objects.bulk_create(
            [
                SimpleCategory(name="first"),
                SimpleCategory(name="second"),
                SimpleCategory(name="third"),
                SimpleCategory(name="fourth"),
            ]
        )