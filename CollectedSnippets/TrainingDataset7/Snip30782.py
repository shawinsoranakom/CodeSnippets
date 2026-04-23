def test_in_subquery(self):
        apple = Food.objects.create(name="apple")
        lunch = Eaten.objects.create(food=apple, meal="lunch")
        self.assertEqual(
            set(Eaten.objects.filter(food__in=Food.objects.filter(name="apple"))),
            {lunch},
        )
        self.assertEqual(
            set(
                Eaten.objects.filter(
                    food__in=Food.objects.filter(name="apple").values("eaten__meal")
                )
            ),
            set(),
        )
        self.assertEqual(
            set(Food.objects.filter(eaten__in=Eaten.objects.filter(meal="lunch"))),
            {apple},
        )