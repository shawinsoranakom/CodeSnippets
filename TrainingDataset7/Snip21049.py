def setUpTestData(cls):
        cls.secondary = Secondary.objects.create(first="a", second="b")
        cls.primary = PrimaryOneToOne.objects.create(
            name="Bella", value="Baxter", related=cls.secondary
        )