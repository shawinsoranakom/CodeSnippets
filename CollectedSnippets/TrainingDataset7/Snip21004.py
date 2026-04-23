def setUpTestData(cls):
        cls.s1 = Secondary.objects.create(first="x1", second="y1")
        cls.p1 = Primary.objects.create(name="p1", value="xx", related=cls.s1)
        cls.p2 = Primary.objects.create(name="p2", value="yy", related=cls.s1)