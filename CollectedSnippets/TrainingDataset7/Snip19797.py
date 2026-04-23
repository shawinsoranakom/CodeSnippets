def setUpTestData(cls):
        cls.p1 = UniqueConstraintProduct.objects.create(name="p1", color="red")
        cls.p2 = UniqueConstraintProduct.objects.create(name="p2")