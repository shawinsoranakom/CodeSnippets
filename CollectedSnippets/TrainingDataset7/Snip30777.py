def test_empty_sliced_subquery(self):
        self.assertEqual(
            Eaten.objects.filter(food__in=Food.objects.all()[0:0]).count(), 0
        )