def test_reverse_in(self):
        apple = Food.objects.create(name="apple")
        pear = Food.objects.create(name="pear")
        lunch_apple = Eaten.objects.create(food=apple, meal="lunch")
        lunch_pear = Eaten.objects.create(food=pear, meal="dinner")

        self.assertEqual(
            set(Food.objects.filter(eaten__in=[lunch_apple, lunch_pear])), {apple, pear}
        )