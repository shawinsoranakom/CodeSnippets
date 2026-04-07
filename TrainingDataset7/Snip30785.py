def test_single_object(self):
        apple = Food.objects.create(name="apple")
        lunch = Eaten.objects.create(food=apple, meal="lunch")
        dinner = Eaten.objects.create(food=apple, meal="dinner")

        self.assertEqual(set(Eaten.objects.filter(food=apple)), {lunch, dinner})