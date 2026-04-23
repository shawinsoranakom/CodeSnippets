def setUpTestData(cls):
        NamedCategory.objects.create(id=1, name="first")
        NamedCategory.objects.create(id=2, name="second")
        NamedCategory.objects.create(id=3, name="third")
        NamedCategory.objects.create(id=4, name="fourth")