def setUpTestData(cls):
        cls.s1 = Secondary.objects.create(first="x1", second="y1")
        BigChild.objects.create(name="b1", value="foo", related=cls.s1, other="bar")