def test_empty_sliced_subquery_exclude(self):
        self.assertEqual(
            Eaten.objects.exclude(food__in=Food.objects.all()[0:0]).count(), 1
        )