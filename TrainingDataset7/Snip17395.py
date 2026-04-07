def setUpTestData(cls):
        cls.s1 = SimpleModel.objects.create(
            field=1,
            created=datetime(2022, 1, 1, 0, 0, 0),
        )
        cls.s2 = SimpleModel.objects.create(
            field=2,
            created=datetime(2022, 1, 1, 0, 0, 1),
        )
        cls.s3 = SimpleModel.objects.create(
            field=3,
            created=datetime(2022, 1, 1, 0, 0, 2),
        )
        cls.r1 = RelatedModel.objects.create(simple=cls.s1)
        cls.r2 = RelatedModel.objects.create(simple=cls.s2)
        cls.r3 = RelatedModel.objects.create(simple=cls.s3)