def test_select_for_update_with_limit(self):
        other = Person.objects.create(name="Grappeli", born=self.city1, died=self.city2)
        with transaction.atomic():
            qs = list(Person.objects.order_by("pk").select_for_update()[1:2])
            self.assertEqual(qs[0], other)