def setUpTestData(cls):
        cls.n = Number.objects.create(integer=42, float=15.5)
        cls.n1 = Number.objects.create(integer=-42, float=-15.5)