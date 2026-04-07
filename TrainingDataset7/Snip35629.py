def setUpTestData(cls):
        cls.d0 = DataPoint.objects.create(name="d0", value="apple")
        cls.d2 = DataPoint.objects.create(name="d2", value="banana")
        cls.d3 = DataPoint.objects.create(name="d3", value="banana", is_active=False)
        cls.r1 = RelatedPoint.objects.create(name="r1", data=cls.d3)