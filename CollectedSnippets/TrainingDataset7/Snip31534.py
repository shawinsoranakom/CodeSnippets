def test_for_update_of_followed_by_values(self):
        with transaction.atomic():
            values = list(Person.objects.select_for_update(of=("self",)).values("pk"))
        self.assertEqual(values, [{"pk": self.person.pk}])