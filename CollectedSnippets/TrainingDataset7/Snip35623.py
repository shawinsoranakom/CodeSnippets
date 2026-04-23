def setUpTestData(cls):
        cls.a1 = A.objects.create()
        cls.a2 = A.objects.create()
        B.objects.bulk_create(B(a=cls.a1) for _ in range(20))
        for x in range(20):
            D.objects.create(a=cls.a1)