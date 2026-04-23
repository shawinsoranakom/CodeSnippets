def test_to_field(self):
        apple = Food.objects.create(name="apple")
        e1 = Eaten.objects.create(food=apple, meal="lunch")
        e2 = Eaten.objects.create(meal="lunch")
        self.assertSequenceEqual(
            Eaten.objects.filter(food__isnull=False),
            [e1],
        )
        self.assertSequenceEqual(
            Eaten.objects.filter(food__isnull=True),
            [e2],
        )