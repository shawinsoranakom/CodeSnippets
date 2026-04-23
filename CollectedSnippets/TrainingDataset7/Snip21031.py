def setUpTestData(cls):
        cls.s1 = Secondary.objects.using("other").create(first="x1", second="y1")
        cls.p1 = Primary.objects.using("other").create(
            name="p1", value="xx", related=cls.s1
        )
        cls.p2 = Primary.objects.using("other").create(
            name="p2", value="yy", related=cls.s1
        )