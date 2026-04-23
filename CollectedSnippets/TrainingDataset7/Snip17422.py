def setUpTestData(cls):
        cls.mtm1 = ManyToManyModel.objects.create()
        cls.s1 = SimpleModel.objects.create(field=0)
        cls.mtm2 = ManyToManyModel.objects.create()
        cls.mtm2.simples.set([cls.s1])