def setUpTestData(cls):
        cls.s1 = SimpleModel.objects.create(field=0)
        cls.s2 = SimpleModel.objects.create(field=1)
        cls.r1 = RelatedModel.objects.create(simple=cls.s1)